# Copyright (c) Microsoft. All rights reserved.

"""
Microsoft UAE Executive Intelligence Brief — 21 Sequential Agents
==================================================================

COLLECTION LAYER (Agents 1–10)
  Agent 1   →  DateIntelligenceAgent         (FoundryChatClient + @tool) — weekly date range
  Agent 2   →  MicrosoftSourceAgent          (FoundryAgent service) — MS first-party RSS via MCP
  Agent 3   →  MicrosoftLearnAgent           (FoundryAgent service) — MS Learn / Docs via MCP
  Agent 4   →  MicrosoftAICloudAgent         (FoundryChatClient + Tavily MCP) — Azure AI, Copilot
  Agent 5   →  MicrosoftProductsAgent        (FoundryChatClient + Tavily MCP) — M365, Teams, GitHub
  Agent 6   →  IndustryAIAgent               (FoundryChatClient + Tavily MCP) — Google AI, Meta, Anthropic
  Agent 7   →  CloudInfraNewsAgent           (FoundryChatClient + Tavily MCP) — AWS, GCP, multi-cloud
  Agent 8   →  UAERegionalTechAgent          (FoundryChatClient + Tavily MCP) — UAE/GCC/MENA tech
  Agent 9   →  GlobalEnterpriseNewsAgent     (FoundryChatClient + Tavily MCP) — CIO/CTO enterprise tech
  Agent 10  →  MarketIntelligenceAgent       (FoundryChatClient + Tavily MCP) — Gartner, Forrester, IDC

  [consolidate_articles() — merges all 10 collection outputs into raw_articles_json]

ANALYSIS LAYER (Agents 11–19)
  Agent 11  →  DeduplicationAgent            (FoundryChatClient) — cluster + deduplicate
  Agent 12  →  ValidationAgent               (FoundryChatClient) — quality filter
  Agent 13  →  TopicIntelligenceAgent        (FoundryChatClient) — summaries + 7-category
  Agent 14  →  MicrosoftMessagingAgent       (FoundryChatClient) — adds microsoft_perspective
  Agent 15  →  UAEImpactAgent                (FoundryChatClient) — adds uae_impact fields
  Agent 16  →  SalesPositioningAgent         (FoundryChatClient) — adds seller_guidance
  Agent 17  →  PriorityScoringAgent          (FoundryChatClient) — score 0-100, sorts descending
  Agent 18  →  NewsletterStructuringAgent    (FoundryChatClient) — field mapping, validation
  Agent 19  →  NewsletterCompositionAgent    (FoundryChatClient) — executive summary + narrative polish

RENDERING & DELIVERY (Agents 20–21)
  Agent 20  →  HTMLRenderingAgent            (AnthropicClient) — polished HTML newsletter
  Agent 21  →  EmailDeliveryWorkIQAgent      (FoundryAgent service) — Outlook delivery via Work IQ

NEWSLETTER CATEGORIES
  - Microsoft AI & Cloud
  - Microsoft Products
  - Industry AI
  - Cloud & Infrastructure
  - UAE & Regional Tech
  - Enterprise Technology
  - Analyst Intelligence
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient, FoundryAgent
from anthropic import AsyncAnthropic
from azure.identity import DefaultAzureCredential

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

NEWSLETTER_RECIPIENT     = os.getenv("NEWSLETTER_RECIPIENT_EMAIL", "Rami.Sarieddine@microsoft.com")
FOUNDRY_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
FOUNDRY_MODEL            = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")
TAVILY_API_KEY           = os.getenv("TAVILY_API_KEY", "")
TAVILY_MCP_URL           = f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"

# Agents 2 & 3: FoundryAgent — service-managed, deployed in Azure AI Foundry
MICROSOFT_SOURCE_AGENT_NAME    = os.getenv("MICROSOFT_SOURCE_AGENT_NAME", "MicrosoftSourceAgent")
MICROSOFT_SOURCE_AGENT_VERSION = os.getenv("MICROSOFT_SOURCE_AGENT_VERSION", "2")
MICROSOFT_LEARN_AGENT_NAME     = os.getenv("MICROSOFT_LEARN_AGENT_NAME", "MicrosoftLearnAgent")
MICROSOFT_LEARN_AGENT_VERSION  = os.getenv("MICROSOFT_LEARN_AGENT_VERSION", "1")

# Agent 21: FoundryAgent — service-managed
EMAIL_DELIVERY_AGENT_NAME    = os.getenv("EMAIL_DELIVERY_WORKIQ_AGENT_NAME", "EmailDeliveryWorkIQAgent")
EMAIL_DELIVERY_AGENT_VERSION = os.getenv("EMAIL_DELIVERY_WORKIQ_AGENT_VERSION", "1")

# Agent 20 (HTML rendering): Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = os.getenv("ANTHROPIC_CHAT_MODEL_ID", "claude-sonnet-4-6")

# Output directory for checkpoints
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPTS_DIR = Path("./prompts")


# ---------------------------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------------------------

def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"Prompt file not found: {path}")


# Lazy-load prompts (so missing files fail at runtime, not import time)
def _prompts():
    return {
        "agent01": load_prompt("agent01_date_intelligence.txt"),
        "agent04": load_prompt("agent04_microsoft_ai_cloud.txt"),
        "agent05": load_prompt("agent05_microsoft_products.txt"),
        "agent06": load_prompt("agent06_industry_ai.txt"),
        "agent07": load_prompt("agent07_cloud_infra_news.txt"),
        "agent08": load_prompt("agent08_uae_regional_tech.txt"),
        "agent09": load_prompt("agent09_global_enterprise_news.txt"),
        "agent10": load_prompt("agent10_market_intelligence.txt"),
        "agent11": load_prompt("agent11_deduplication.txt"),
        "agent12": load_prompt("agent12_validation.txt"),
        "agent13": load_prompt("agent13_topic_intelligence.txt"),
        "agent14": load_prompt("agent14_microsoft_messaging.txt"),
        "agent15": load_prompt("agent15_uae_impact.txt"),
        "agent16": load_prompt("agent16_sales_positioning.txt"),
        "agent17": load_prompt("agent17_priority_scoring.txt"),
        "agent18": load_prompt("agent18_newsletter_structuring.txt"),
        "agent19": load_prompt("agent19_newsletter_composition.txt"),
        "agent21": load_prompt("agent21_html_rendering.txt"),
    }


# ---------------------------------------------------------------------------
# GA @tool — get current date
# ---------------------------------------------------------------------------

@tool(approval_mode="never_require")
def get_current_date() -> str:
    """Returns today's date in YYYY-MM-DD format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _checkpoint(step: int, name: str, text: str) -> None:
    safe = name.replace(" ", "")
    path = OUTPUT_DIR / f"checkpoint_{step:02d}_{safe}.json"
    path.write_text(text, encoding="utf-8")
    print(f"  [✓ checkpoint {step:02d}] saved → {path.name}")


def _load_checkpoint(step: int, name: str) -> Optional[str]:
    safe = name.replace(" ", "")
    path = OUTPUT_DIR / f"checkpoint_{step:02d}_{safe}.json"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        if content:
            print(f"  [↩ checkpoint {step:02d}] {name} — resuming from {path.name}  (skipping agent)")
            return content
    return None


# ---------------------------------------------------------------------------
# Result extraction helper
# ---------------------------------------------------------------------------

def _extract_text_from_result(result) -> str:
    """Extract text from MAF agent result (GA or legacy shape)."""
    # GA shape: result.text
    if hasattr(result, "text") and result.text:
        return result.text
    # Legacy shape: result.messages[].contents[].text
    try:
        if hasattr(result, "messages") and result.messages:
            for message in reversed(result.messages):
                if hasattr(message, "contents"):
                    for content in message.contents:
                        if getattr(content, "type", None) == "text":
                            if hasattr(content, "text") and content.text:
                                return content.text
    except Exception:
        pass
    return str(result)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _safe_json_parse(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        # Try to extract JSON from markdown fences
        import re
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None


def consolidate_articles(agent_outputs: dict) -> dict:
    """Merge raw JSON outputs from agents 1–10 into a unified article list."""
    all_articles = []
    for agent_label, raw_text in agent_outputs.items():
        if not raw_text:
            continue
        data = _safe_json_parse(raw_text)
        if not data:
            continue
        # Agents may return {"results": [...]} or {"articles": [...]}
        items = data.get("results", []) or data.get("articles", [])
        for item in items:
            if not item.get("url") or not item.get("title"):
                continue
            all_articles.append({
                "title":             item.get("title", ""),
                "url":               item.get("url", ""),
                "date":              item.get("date", ""),
                "source":            item.get("source", ""),
                "collection_source": agent_label,
                "snippet":           item.get("snippet", ""),
                "topic":             item.get("topic", ""),
                "images":            item.get("images", []),
                "favicon":           item.get("favicon", ""),
            })
    return {"all_articles": all_articles, "total_count": len(all_articles)}


# ---------------------------------------------------------------------------
# Main workflow class
# ---------------------------------------------------------------------------

class MicrosoftIntelligenceWorkflow:

    def __init__(self) -> None:
        self._credential       = DefaultAzureCredential(
            additionally_allowed_tenants=["*"],
            process_timeout=60,  # allow az CLI up to 60s to return a token
        )
        self._project_endpoint = FOUNDRY_PROJECT_ENDPOINT
        self._model            = FOUNDRY_MODEL

    # ------------------------------------------------------------------
    # Client factory
    # ------------------------------------------------------------------

    def _make_foundry_client(self) -> FoundryChatClient:
        return FoundryChatClient(
            project_endpoint=self._project_endpoint,
            model=self._model,
            credential=self._credential,
        )

    # ------------------------------------------------------------------
    # Agent call helpers
    # ------------------------------------------------------------------

    async def _call_foundry_service_agent(
        self,
        agent_name: str,
        agent_version: str,
        label: str,
        step: int,
        query: str,
    ) -> str:
        """Call a pre-deployed Foundry service agent (FoundryAgent)."""
        print(f"\n[{step}/21] {label} — FoundryAgent ({agent_name} v{agent_version})...")
        agent = FoundryAgent(
            project_endpoint=self._project_endpoint,
            agent_name=agent_name,
            agent_version=agent_version,
            credential=self._credential,
        )
        result = await agent.run(query)
        return _extract_text_from_result(result)

    async def _run_tavily_search_agent(
        self,
        instructions: str,
        agent_label: str,
        step: int,
        query: str,
    ) -> str:
        """Run a FoundryChatClient agent equipped with Tavily MCP (agents 4-10)."""
        print(f"\n[{step}/21] {agent_label} (FoundryChatClient + Tavily MCP)...")
        MAX_RETRIES = 3
        BASE_DELAY  = 60  # seconds

        tavily_tool = {
            "type":            "mcp",
            "server_label":    "tavily",
            "server_url":      TAVILY_MCP_URL,
            "require_approval": "never",
        }

        for attempt in range(MAX_RETRIES):
            try:
                agent = Agent(
                    client=self._make_foundry_client(),
                    instructions=instructions,
                    tools=[tavily_tool],
                )
                result = await agent.run(query)
                text = _extract_text_from_result(result)
                print(f"  [{step}/21] {agent_label} ✓  ({len(text)} chars)")
                return text
            except Exception as exc:
                err = str(exc).lower()
                if "429" in err or "rate" in err or "too many" in err:
                    delay = BASE_DELAY * (2 ** attempt)
                    if attempt < MAX_RETRIES - 1:
                        print(f"  [{step}/21] {agent_label} — 429 rate limit, retrying in {delay}s (attempt {attempt+1}/{MAX_RETRIES})...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"  [{step}/21] {agent_label} — 429 rate limit exhausted, returning empty result")
                        return json.dumps({"results": []})
                else:
                    print(f"  [{step}/21] {agent_label} — error: {exc}")
                    return json.dumps({"results": []})

        return json.dumps({"results": []})

    async def _call_analysis_agent(
        self,
        instructions: str,
        label: str,
        step: int,
        query: str,
    ) -> str:
        """Run a FoundryChatClient agent for analysis (agents 11-19, no external tools)."""
        print(f"\n[{step}/21] {label} (FoundryChatClient)...")
        MAX_RETRIES = 3
        BASE_DELAY  = 60

        for attempt in range(MAX_RETRIES):
            try:
                agent = Agent(
                    client=self._make_foundry_client(),
                    instructions=instructions,
                    tools=[],
                )
                result = await agent.run(query)
                text = _extract_text_from_result(result)
                print(f"  [{step}/21] {label} ✓  ({len(text)} chars)")
                return text
            except Exception as exc:
                err = str(exc).lower()
                if "429" in err or "rate" in err or "too many" in err:
                    delay = BASE_DELAY * (2 ** attempt)
                    if attempt < MAX_RETRIES - 1:
                        print(f"  [{step}/21] {label} — 429, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"  [{step}/21] {label} — 429 exhausted, returning empty")
                        return "{}"
                else:
                    print(f"  [{step}/21] {label} — error: {exc}")
                    raise

        return "{}"

    # ------------------------------------------------------------------
    # HTML rendering (Anthropic)
    # ------------------------------------------------------------------

    async def _run_html_rendering(self, composition_text: str, prompts: dict) -> str:
        """Agent 20: Extract images from article data, then render HTML via Anthropic SDK."""
        print(f"\n[20/21] HTMLRenderingAgent (Anthropic SDK — {ANTHROPIC_MODEL})...")

        # Extract image URLs from collected article data for inline rendering
        newsletter_data     = _safe_json_parse(composition_text) or {}
        newsletter_sections = newsletter_data.get("newsletter_sections", {})
        for topic in newsletter_sections.get("topics", []):
            for article in topic.get("articles", []):
                images = article.get("images", [])
                if images and images[0].get("url", "").startswith("http"):
                    topic.setdefault("image_url",     images[0]["url"])
                    topic.setdefault("image_caption",
                        images[0].get("description", "") or article.get("title", ""))
                    break

        enriched_text = json.dumps(newsletter_data, ensure_ascii=False)

        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8192,
            system=prompts["agent21"],
            messages=[{"role": "user", "content": enriched_text}],
        )
        text = message.content[0].text if message.content else ""
        print(f"  [20/21] HTMLRenderingAgent ✓  ({len(text)} chars)")
        return text

    # ------------------------------------------------------------------
    # Main execute()
    # ------------------------------------------------------------------

    async def execute(self) -> None:
        print("=" * 70)
        print("Microsoft UAE Executive Intelligence Brief")
        print(f"Started: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        prompts = _prompts()

        # ----------------------------------------------------------------
        # AGENT 1 — Date Intelligence
        # ----------------------------------------------------------------
        STEP = 0
        cached = _load_checkpoint(STEP, "raw_articles_json")
        raw_json_text = None

        date_text = _load_checkpoint(1, "DateIntelligence")
        if not date_text:
            print(f"\n[1/21] DateIntelligenceAgent (FoundryChatClient + @tool)...")
            agent1 = Agent(
                client=self._make_foundry_client(),
                instructions=prompts["agent01"],
                tools=[get_current_date],
            )
            result = await agent1.run("Determine the date range for this week's newsletter.")
            date_text = _extract_text_from_result(result)
            print(f"  [1/21] DateIntelligenceAgent ✓  ({len(date_text)} chars)")
            _checkpoint(1, "DateIntelligence", date_text)

        date_data   = _safe_json_parse(date_text) or {}
        start_date  = date_data.get("start_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        end_date    = date_data.get("end_date",   datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        interval    = date_data.get("interval_label", "Last 7 days")
        date_query  = json.dumps({"start_date": start_date, "end_date": end_date, "interval_label": interval})
        print(f"  Date range: {start_date} → {end_date}  ({interval})")

        # ----------------------------------------------------------------
        # Skip collection if we already have raw_articles checkpoint
        # ----------------------------------------------------------------
        if cached:
            raw_json_text = cached
        else:
            # AGENT 2 — MicrosoftSourceAgent (FoundryAgent service)
            ms_source_text = _load_checkpoint(2, "MicrosoftSource")
            if not ms_source_text:
                ms_source_text = await self._call_foundry_service_agent(
                    MICROSOFT_SOURCE_AGENT_NAME, MICROSOFT_SOURCE_AGENT_VERSION,
                    "MicrosoftSourceAgent", 2, date_query,
                )
                _checkpoint(2, "MicrosoftSource", ms_source_text)

            # AGENT 3 — MicrosoftLearnAgent (FoundryAgent service)
            ms_learn_text = _load_checkpoint(3, "MicrosoftLearn")
            if not ms_learn_text:
                ms_learn_text = await self._call_foundry_service_agent(
                    MICROSOFT_LEARN_AGENT_NAME, MICROSOFT_LEARN_AGENT_VERSION,
                    "MicrosoftLearnAgent", 3, date_query,
                )
                _checkpoint(3, "MicrosoftLearn", ms_learn_text)

            # AGENTS 4–10 — Tavily MCP search agents
            tavily_configs = [
                (4,  "MicrosoftAICloud",       prompts["agent04"]),
                (5,  "MicrosoftProducts",       prompts["agent05"]),
                (6,  "IndustryAI",              prompts["agent06"]),
                (7,  "CloudInfraNews",          prompts["agent07"]),
                (8,  "UAERegionalTech",         prompts["agent08"]),
                (9,  "GlobalEnterpriseNews",    prompts["agent09"]),
                (10, "MarketIntelligence",      prompts["agent10"]),
            ]

            tavily_results = {}
            for step, label, instructions in tavily_configs:
                text = _load_checkpoint(step, label)
                if not text:
                    text = await self._run_tavily_search_agent(instructions, label, step, date_query)
                    _checkpoint(step, label, text)
                tavily_results[label] = text

            # Consolidate all collection outputs
            all_outputs = {
                "MicrosoftSource": ms_source_text,
                "MicrosoftLearn":  ms_learn_text,
                **tavily_results,
            }
            consolidated = consolidate_articles(all_outputs)
            raw_json_text = json.dumps(consolidated, ensure_ascii=False)
            _checkpoint(0, "raw_articles_json", raw_json_text)
            print(f"\n  Consolidated {consolidated['total_count']} articles from all collection agents.")

        # ----------------------------------------------------------------
        # ANALYSIS LAYER — Agents 11–19
        # ----------------------------------------------------------------

        analysis_steps = [
            (11, "Deduplication",          "agent11"),
            (12, "Validation",             "agent12"),
            (13, "TopicIntelligence",      "agent13"),
            (14, "MicrosoftMessaging",     "agent14"),
            (15, "UAEImpact",              "agent15"),
            (16, "SalesPositioning",       "agent16"),
            (17, "PriorityScoring",        "agent17"),
            (18, "NewsletterStructuring",  "agent18"),
            (19, "NewsletterComposition",  "agent19"),
        ]

        current_text = raw_json_text

        for step, label, prompt_key in analysis_steps:
            cached_step = _load_checkpoint(step, label)
            if cached_step:
                current_text = cached_step
                continue

            # Slim payload for deduplication to reduce token usage
            if step == 11:
                raw_data = _safe_json_parse(current_text) or {}
                slim_articles = [
                    {
                        "title":  a.get("title", ""),
                        "url":    a.get("url", ""),
                        "topic":  a.get("topic", ""),
                        "source": a.get("source", ""),
                        "date":   a.get("date", ""),
                    }
                    for a in raw_data.get("all_articles", [])
                ]
                query_text = json.dumps({"all_articles": slim_articles}, ensure_ascii=False)
            else:
                query_text = current_text

            current_text = await self._call_analysis_agent(
                prompts[prompt_key], label, step, query_text,
            )
            _checkpoint(step, label, current_text)

        composition_text = current_text

        # ----------------------------------------------------------------
        # AGENT 20 — HTML Rendering (Anthropic)
        # ----------------------------------------------------------------
        html_text = _load_checkpoint(20, "HTMLRendering")
        if not html_text:
            html_text = await self._run_html_rendering(composition_text, prompts)
            _checkpoint(20, "HTMLRendering", html_text)

        # ----------------------------------------------------------------
        # AGENT 21 — Email Delivery (FoundryAgent service)
        # ----------------------------------------------------------------
        email_cached = _load_checkpoint(21, "EmailDelivery")
        if not email_cached:
            email_query = json.dumps({
                "recipient":   NEWSLETTER_RECIPIENT,
                "subject":     f"Microsoft UAE Executive Intelligence Brief — {end_date}",
                "html_body":   html_text,
            }, ensure_ascii=False)

            await self._call_foundry_service_agent(
                EMAIL_DELIVERY_AGENT_NAME, EMAIL_DELIVERY_AGENT_VERSION,
                "EmailDeliveryWorkIQAgent", 21, email_query,
            )
            _checkpoint(21, "EmailDelivery", f'{{"status":"sent","recipient":"{NEWSLETTER_RECIPIENT}"}}')

        print("\n" + "=" * 70)
        print(f"Newsletter delivered to {NEWSLETTER_RECIPIENT}")
        print(f"Completed: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    workflow = MicrosoftIntelligenceWorkflow()
    await workflow.execute()


if __name__ == "__main__":
    asyncio.run(main())
