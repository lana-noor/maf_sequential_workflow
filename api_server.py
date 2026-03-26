"""
FastAPI backend with Server-Sent Events for the Payslip Verification UI.

Run with:
    uvicorn api_server:app --reload --port 8000
"""
import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from payslip_verification_workflow import (
    PayslipWorkflowExecutor,
    SAMPLE_SALARY_SLIP_MARKDOWN,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Payslip Verification API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Holds the path to the most-recently generated Word document so the
# download endpoint can serve it without storing state in the request.
_last_word_doc: dict = {"path": None}


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    salary_slip: str = SAMPLE_SALARY_SLIP_MARKDOWN


# ---------------------------------------------------------------------------
# Streaming executor — subclasses the workflow to inject SSE events
# ---------------------------------------------------------------------------

class StreamingWorkflowExecutor(PayslipWorkflowExecutor):
    """Overrides agent runner methods to emit progress events into a queue."""

    def __init__(self, queue: asyncio.Queue) -> None:
        super().__init__()
        self._q = queue

    async def _emit(self, data: dict) -> None:
        await self._q.put(data)

    # Agent 1 — Document Verification
    async def _run_verification(self, salary_slip_input: str) -> str:
        await self._emit({"event": "agent_start", "agent": 1})
        result = await super()._run_verification(salary_slip_input)
        await self._emit({"event": "agent_complete", "agent": 1, "output": result})
        return result

    # Agent 2 — Salary Analysis (code interpreter)
    async def _run_analysis(self, salary_slip_input: str, employee_name: str) -> str:
        await self._emit({"event": "agent_start", "agent": 2, "employee": employee_name})
        result = await super()._run_analysis(salary_slip_input, employee_name)
        await self._emit({"event": "agent_complete", "agent": 2, "output": result})
        return result

    # Agent 3 — Document Summary  (also signals executor_start on return,
    # because the base execute() saves files immediately after this method)
    async def _run_summary(self, verification_text: str, analysis_text: str) -> str:
        await self._emit({"event": "agent_start", "agent": 3})
        result = await super()._run_summary(verification_text, analysis_text)
        await self._emit({"event": "agent_complete", "agent": 3, "output": result})
        await self._emit({"event": "executor_start"})   # file-saving is next
        return result

    # Full workflow — wraps super().execute() and emits completion events
    async def execute(self, salary_slip_input: str) -> dict:
        result = await super().execute(salary_slip_input)
        await self._emit({
            "event": "executor_complete",
            "markdown": result["summary"],
            "word_doc_path": result.get("word_doc_path") or "",
        })
        await self._emit({"event": "done"})
        return result


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------

@app.post("/api/run")
async def run_workflow(body: RunRequest) -> StreamingResponse:
    """
    Run the payslip verification workflow and stream progress as SSE events.

    Event types emitted:
      agent_start       { agent: 1|2|3 }
      agent_complete    { agent: 1|2|3, output: str }
      executor_start    {}
      executor_complete { markdown: str, word_doc_path: str }
      done              {}
      error             { message: str }
    """

    async def generate() -> AsyncIterator[str]:
        queue: asyncio.Queue = asyncio.Queue()
        executor = StreamingWorkflowExecutor(queue)

        async def run_task() -> None:
            try:
                result = await executor.execute(body.salary_slip)
                _last_word_doc["path"] = result.get("word_doc_path")
            except Exception as exc:
                await queue.put({"event": "error", "message": str(exc)})
                await queue.put({"event": "done"})

        task = asyncio.create_task(run_task())

        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event") in ("done", "error"):
                    break
        finally:
            await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Word doc download endpoint
# ---------------------------------------------------------------------------

@app.get("/api/download")
async def download_word() -> FileResponse:
    path = _last_word_doc.get("path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Word document not yet generated")
    return FileResponse(
        path=path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(path).name,
    )


# ---------------------------------------------------------------------------
# Sample slip endpoint — used to pre-fill the React textarea
# ---------------------------------------------------------------------------

@app.get("/api/sample")
async def get_sample() -> dict:
    return {"content": SAMPLE_SALARY_SLIP_MARKDOWN}
