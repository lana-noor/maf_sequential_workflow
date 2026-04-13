# Microsoft Agent Framework Budget Variance Analysis Sequential Agent Workflow

> **A reusable multi-agent workflow framework** built with Microsoft Foundry Agent Service that demonstrates how to orchestrate specialized agents with different tools to solve complex business problems. This prototype showcases budget variance analysis for government agencies, but the **sequential agent pattern is designed to be adapted for any domain or use case**.
>
> **🛠️ Demonstrates Integration of 5 Key Agent Tools:**
> - **Custom MCP Server** - Serve domain-specific data from any source
> - **Code Interpreter** - Analyze structured data (CSV, Excel, databases)
> - **Foundry IQ (Azure AI Search)** - Retrieve policy, compliance, or knowledge documents
> - **Work IQ (Microsoft 365)** - Automate email, calendar, Teams notifications
> - **Web Search (Bing)** - Gather real-time external context and validation
>
> **🎯 Perfect for building your own workflows:** Mix and match these tools to create agents tailored to your specific business requirements—whether it's compliance auditing, financial reporting, customer service automation, or operational intelligence.

---

## 🎯 Overview

This workflow demonstrates a **public finance use case**: automating quarterly budget variance analysis for the **Apex Digital Government Authority (ADGA)** (Fake company name) using a 6-agent sequential pipeline.

### What It Does

**The workflow performs 3-way reconciliation:**
1. **Department Claims** (what departments SAY happened) → via MCP server
2. **Economic Validation** (external data confirms/contradicts) → via Web Search
3. **Official Data** (what ACTUALLY happened) → via CSV file analysis
4. **Policy Compliance** (what regulations REQUIRE) → via AI Search

**Output:** A comprehensive executive report (Markdown + Word) delivered via Outlook and a Generated word document. 

### Key Features

✅ **Model Context Protocol (MCP)** - Custom server deployed to Azure Container Apps  
✅ **Web Search Integration** - Real-time economic data validation  
✅ **Code Interpreter** - Python-based CSV analysis with file attachments  
✅ **Foundry IQ (AI Search)** - RAG over policy documents  
✅ **Microsoft 365** - Automated email delivery via Outlook  
✅ **Sequential Agent Orchestration** - Each agent builds on previous outputs  
✅ **Enterprise-Ready** - Handles real CSV data, generates audit-ready reports

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BUDGET VARIANCE WORKFLOW                         │
│                  (6 Sequential Agents + MCP Server)                 │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  📦 Azure Container Apps                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MCP Server: budget-reports-mcp-server                         │ │
│  │  Serves: department_reports/*.md (narratives & justifications) │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 1: BudgetReportsMCPAgent                                     │
│  Tool: MCP                                                          │
│  Output: Department claims & justifications (JSON)                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 2: WebSearchBudgetsAgent                                     │
│  Tool: Web Search (Bing Grounding)                                  │
│  Output: Economic validation data (inflation, cloud costs, etc.)   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 3: BudgetVarianceCodeIntAgent                                │
│  Tool: Code Interpreter                                             │
│  Files: approved_budgets.csv, historical_actuals.csv                │
│  Output: Reconciliation analysis (claims vs. reality) + policy check│
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 4: BudgetPolicyAgent                                         │
│  Tool: Azure AI Search (Foundry IQ)                                 │
│  Index: adga-budget-policies                                        │
│  Output: Compliance requirements, regulatory risks, timelines       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 5: Summary Agent                                             │
│  Tool: Responses API (no agent_reference)                           │
│  Output: Executive Markdown report → Word document                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 6: BudgetWorkIQMailAgent                                     │
│  Tool: Microsoft 365 (Outlook)                                      │
│  Output: Email sent to CFO/Board with report attached               │
└─────────────────────────────────────────────────────────────────────┘
```

### Interactive Architecture Diagram

```mermaid
graph TB
    Start([🚀 Start Workflow])

    subgraph ACA["☁️ Azure Container Apps"]
        MCP[MCP Server<br/>budget-reports-mcp-server<br/>📁 department_reports/*.md]
    end

    subgraph Agent1["🤖 Agent 1: BudgetReportsMCPAgent"]
        A1[Tool: MCP<br/>Version: 3<br/><br/>📥 Retrieves department<br/>narrative reports<br/><br/>📤 Output: Department claims JSON]
    end

    subgraph Agent2["🤖 Agent 2: WebSearchBudgetsAgent"]
        A2[Tool: Web Search Bing<br/>Version: 14<br/><br/>🔍 Searches economic data<br/>inflation, cloud costs<br/><br/>📤 Output: Validation JSON<br/>CONFIRMS/CONTRADICTS]
    end

    subgraph Agent3["🤖 Agent 3: BudgetVarianceCodeIntAgent"]
        A3[Tool: Code Interpreter<br/>Version: 4<br/><br/>📊 Analyzes CSV files<br/>approved_budgets.csv<br/>historical_actuals.csv<br/><br/>📤 Output: Reconciliation JSON<br/>Claims vs Reality]
        CSV1[(approved_budgets.csv)]
        CSV2[(historical_actuals.csv)]
        CSV1 --> A3
        CSV2 --> A3
    end

    subgraph Agent4["🤖 Agent 4: BudgetPolicyAgent"]
        A4[Tool: Azure AI Search<br/>Version: 1<br/><br/>📚 Queries policy docs<br/>adga-budget-policies<br/><br/>📤 Output: Policy guidance JSON<br/>Compliance requirements]
        AISearch[(Azure AI Search<br/>adga-budget-policies<br/>Financial Act<br/>IT Guidelines<br/>Procurement Rules)]
        AISearch --> A4
    end

    subgraph Agent5["🤖 Agent 5: Summary Agent"]
        A5[Tool: Responses API<br/>No agent_reference<br/><br/>📝 Synthesizes all outputs<br/>Agents 1-4<br/><br/>📤 Output: Executive Report<br/>Markdown + Word DOCX]
    end

    subgraph Agent6["🤖 Agent 6: BudgetWorkIQMailAgent"]
        A6[Tool: Microsoft 365<br/>Version: 7<br/><br/>📧 Sends email via Outlook<br/>Routes by severity<br/><br/>📤 Output: Delivery confirmation]
    end

    End([✅ Report Delivered<br/>to CFO/Board])

    Start --> MCP
    MCP --> A1
    A1 --> |Department Claims<br/>Justifications| A2
    A2 --> |Economic Validation<br/>External Data| A3
    A3 --> |Reconciliation<br/>Policy Status| A4
    A4 --> |Compliance<br/>Requirements| A5
    A5 --> |Executive Report<br/>MD + DOCX| A6
    A6 --> End

    classDef mcpStyle fill:#4A90E2,stroke:#2E5C8A,color:#fff,stroke-width:2px
    classDef agent1Style fill:#9B59B6,stroke:#6C3483,color:#fff,stroke-width:2px
    classDef agent2Style fill:#3498DB,stroke:#2471A3,color:#fff,stroke-width:2px
    classDef agent3Style fill:#E67E22,stroke:#AF601A,color:#fff,stroke-width:2px
    classDef agent4Style fill:#1ABC9C,stroke:#117A65,color:#fff,stroke-width:2px
    classDef agent5Style fill:#F39C12,stroke:#B9770E,color:#fff,stroke-width:2px
    classDef agent6Style fill:#E74C3C,stroke:#A93226,color:#fff,stroke-width:2px
    classDef dataStyle fill:#7B68EE,stroke:#5A4CAA,color:#fff,stroke-width:2px
    classDef startEndStyle fill:#27AE60,stroke:#1E8449,color:#fff,stroke-width:3px

    class MCP mcpStyle
    class A1 agent1Style
    class A2 agent2Style
    class A3 agent3Style
    class A4 agent4Style
    class A5 agent5Style
    class A6 agent6Style
    class CSV1,CSV2,AISearch dataStyle
    class Start,End startEndStyle
```

---

## 🤖 The 6 Agents

### Agent 1: **BudgetReportsMCPAgent**
**Foundry Agent Name:** `BudgetReportsMCPAgent` (version 3)
**Tool:** Model Context Protocol (MCP)
**MCP Endpoint:** Azure Container Apps deployment

**Purpose:** Retrieves department-submitted narrative variance reports containing justifications, claims, and remediation plans.

**What it retrieves:**
- Department variance narratives (Markdown format)
- Claimed actual spend vs. approved budget
- Justifications (e.g., "Zero Trust mandate", "cloud cost inflation")
- External factors cited (weather, mandates, incidents)
- Proposed remediation actions

**Output Format:** JSON with department claims, justifications, and metadata

**Key Concept:** This represents **what departments CLAIM happened** (not yet verified).

---

### Agent 2: **WebSearchBudgetsAgent**
**Foundry Agent Name:** `WebSearchBudgetsAgent` (version 14)
**Tool:** Web Search (Bing Grounding)

**Purpose:** Validates department claims against real-world economic data.

**What it searches for:**
- UAE inflation rates (Q1 2026)
- Cloud computing cost trends
- Energy price changes
- Cybersecurity incidents in public sector
- Government procurement regulation updates
- HR recruitment market conditions

**Output Format:** JSON with sector trends and claim validation (CONFIRMED/CONTRADICTS/UNCLEAR)

**Example Validation:**
```json
{
  "cloud_computing": {
    "cost_trend": "increasing",
    "yoy_change_pct": 12,
    "validation": "CONFIRMS department claim about +12% cloud inflation"
  }
}
```

---

### Agent 3: **BudgetVarianceCodeIntAgent**
**Foundry Agent Name:** `BudgetVarianceCodeIntAgent` (version 4)
**Tool:** Code Interpreter
**Attached Files:**
- `approved_budgets.csv` (official approved budgets)
- `historical_actuals.csv` (official spending data)

**Purpose:** Analyzes official CSV data to determine **what ACTUALLY happened** and reconciles against department claims.

**What it does:**
1. Loads CSV files using Python (pandas)
2. Calculates actual variances from official data
3. Compares department claims vs. actual figures (discrepancy detection)
4. Applies policy thresholds:
   - ✅ ACCEPTABLE: <5%
   - ⚠️ MINOR: 5-10%
   - 🔶 SIGNIFICANT: 10-25% (requires CFO approval)
   - 🚨 CRITICAL: >25% (requires Board notification)
5. Assesses credibility of justifications using Agent 2's economic data
6. Analyzes historical trends (4-quarter comparison)

**Output Format:** JSON with reconciliation findings, policy status, credibility assessment

**Key Feature:** 3-way reconciliation (claims vs. reality vs. economic context)

---

### Agent 4: **BudgetPolicyAgent** 
**Foundry Agent Name:** `BudgetPolicyAgent` (version 1)
**Tool:** Azure AI Search (Foundry IQ)
**AI Search Index:** `adga-budget-policies`

**Purpose:** Retrieves authoritative policy guidance from ingested regulatory documents.

**Documents Searched:**
- ADGA Financial Management Act 2024
- IT Technology Spending Guidelines 2026
- Public Sector Procurement Guidelines 2026

**What it provides:**
- Specific policy section citations (e.g., "Section 6.3 - Critical Variance Procedures")
- Escalation requirements and timelines
- Approval authorities (CFO vs. Board)
- Sector-specific guidance (IT has modified thresholds)
- Compliance risks and audit implications

**Output Format:** JSON with policy requirements, mandatory actions, timelines

**Example Output:**
```json
{
  "department_code": "IT",
  "variance_pct": 28.4,
  "policy_requirements": {
    "escalation_required": "Board notification within 15 business days",
    "approval_authority": "Board of Directors"
  }
}
```

---

### Agent 5: **Summary Agent** (Not a Foundry Agent type)
**Type:** Responses API (inline agent, not `agent_reference`)
**Tool:** GPT-5-mini via Responses API

**Purpose:** Synthesizes all previous agent outputs into a comprehensive executive report.

**Inputs:**
1. Department claims (Agent 1)
2. Economic validation (Agent 2)
3. Official variance analysis (Agent 3)
4. Policy guidance (Agent 4)

**Outputs:**
1. **Markdown report** with:
   - Executive summary
   - Department-by-department analysis
   - Compliance timeline table
   - Recommendations with rationale
   - Historical trend analysis
2. **Word document (.docx)** for stakeholder distribution

**Report Structure:**
- 📊 Executive Summary
- 💰 Overall Budget Position
- 📋 Department Variance Summary (table)
- 🌍 Economic Context & Claim Validation
- 🔍 Detailed Department Analysis (CRITICAL/SIGNIFICANT only)
- ⚠️ Required Actions & Compliance Timeline
- 💡 Recommendations
- ✅ Audit Trail

---

### Agent 6: **BudgetWorkIQMailAgent**
**Foundry Agent Name:** `BudgetWorkIQMailAgent` (version 7)
**Tool:** Microsoft 365 (Outlook via Microsoft Graph API)

**Purpose:** Distributes the final report to appropriate stakeholders via email.

**Email Routing Logic:**
- **CRITICAL variance** (>25%) → CFO + Board Secretary + Internal Audit
- **SIGNIFICANT variance** (10-25%) → CFO + Finance Director
- **MINOR/ACCEPTABLE** → Finance Director + Budget Manager

**Email Components:**
- Subject line with severity indicator
- Professional body with key highlights
- Attached report (Markdown + Word)
- Importance flag based on severity

**Output Format:** JSON with delivery confirmation, recipients, message ID

---

## 📦 Prerequisites

### Required Azure Resources

1. **Azure AI Foundry Hub + Project**
   - Enable Agent Service
   - GPT-4.1, gpt-5-mini, gpt-5, gpt-5.4 etc.. deployment

2. **Azure Container Registry** (for MCP server)

3. **Azure Container Apps** (for MCP server hosting)

4. **Azure AI Search** (for Foundry IQ / Agent 4)
   - Create index: `adga-budget-policies`
   - Ingest policy documents from `data/foundry_iq_docs/`

5. **Microsoft 365** (for Outlook integration)
   - Outlook connection configured in Agent Service

---

## 🚀 Deployment Guide

### Step 1: Deploy MCP Server to Azure Container Apps

The MCP server provides department narrative reports to Agent 1.

```powershell

# Deploy to Azure (creates resource group, ACR, Container App)
.\deploy-to-aca.ps1
```

**What this does:**
1. Creates Azure Resource Group
2. Creates Azure Container Registry (ACR)
3. Builds Docker image with `budget-reports-mcp-server.py`
4. Pushes image to ACR
5. Creates Container App Environment
6. Deploys Container App with public endpoint

**Expected Output:**
```
✅ Deployment successful!

MCP Server Endpoint:
https://budget-reports-mcp-server.<random-id>.eastus.azurecontainerapps.io/mcp
```

**Save this URL** - you'll need it for Agent 1 configuration.

---

### Step 1.2: Test MCP Server Endpoint

Verify the MCP server is working:

```powershell
# Test the MCP endpoint
.\test-mcp-endpoint.ps1
```

Or use curl:
```bash
curl https://budget-reports-mcp-server.<your-id>.eastus.azurecontainerapps.io/sse
```

You should see: `event: endpoint` response with MCP protocol information.


---
### Step 1.3: Create MCP Server Agent (Agent 1)
Agent 4 requires a custom MCP Server tool. Use the Remote MCP Server and copy it to the agent tool. 

---


### Step 2: Create Foundry IQ Index (Agent 4)

Agent 4 requires an Azure AI Search index with policy documents.

#### 2.1 Create AI Search Index

Run notebook `data/department_reports/create_foundryiq_search_index.ipynb` to create index `budget-reports-workflow-index`

THe notebook ingests these files from `data/foundry_iq_docs/`:
- `ADGA_Financial_Management_Act_2024.md`
- `IT_Technology_Spending_Guidelines_2026.md`
- `Public_Sector_Procurement_Guidelines_2026.md`

---

### Step 3: Create Agents in Azure AI Foundry

Create **5 agents** in the Azure AI Foundry portal with these exact names and configurations:

#### Agent 1: BudgetReportsMCPAgent

```
Name: BudgetReportsMCPAgent
Version: 3
Model: gpt-5-mini (or your deployment)
Tools: ✅ mcp

MCP Configuration:
  Endpoint: https://budget-reports-mcp-server.<your-id>.eastus.azurecontainerapps.io/mcp

Instructions:
  Copy entire content from: prompts/agent1_mcp_data.txt
```

#### Agent 2: WebSearchBudgetsAgent

```
Name: WebSearchBudgetsAgent
Version: 14
Model: gpt-5-mini
Tools: ✅ bing_grounding

Instructions:
  Copy entire content from: prompts/agent2_web_search.txt
```

#### Agent 3: BudgetVarianceCodeIntAgent

```
Name: BudgetVarianceCodeIntAgent
Version: 4
Model: gpt-5
Tools: ✅ code_interpreter

File Attachments:
  ✅ Upload: data/approved_budgets.csv
  ✅ Upload: data/historical_actuals.csv

Instructions:
  Copy entire content from: prompts/agent3_code_interpreter.txt
```

**IMPORTANT:** The CSV files must be uploaded as **attachments** to the agent in the Foundry portal. The agent will automatically have access to these files when running code.

#### Agent 4: BudgetPolicyAgent

```
Create index using the notebook: data/department_reports/create_foundryiq_search_index.ipynb

Name: BudgetPolicyAgent
Version: 1
Model: gpt-5-mini
Tools: ✅ Foundry IQ Knowledgebase 
OR ✅ Azure AI Search as a Foundry tool 

AI Search Configuration:
  Index name: budget-reports-workflow-index 

Instructions:
  Copy entire content from: prompts/agent4_foundry_iq.txt
```

#### Agent 6: BudgetWorkIQMailAgent

```
Name: BudgetWorkIQMailAgent
Version: 7
Model: gpt-5-mini
Tools: ✅ microsoft365 (Outlook connection)

Instructions:
  Copy entire content from: prompts/agent6_outlook.txt
```

---

## ▶️ Running the Workflow

Step 1: Create a `.env` file in the directory:

**Update these values:**
- `AZURE_AI_PROJECT_ENDPOINT` - Your Azure AI Foundry project endpoint
- `MCP_SERVER_URL` - From Step 1 deployment output
- `OUTLOOK_RECIPIENT_EMAIL` - Your email address
- Agent versions - Match what you created in Step 4

Step 2: 
```powershell
# Activate virtual environment (if using one)
uv venv venv 
venv\Scripts\activate

# Log in to Azure 
Azd auth login 

# Install required packages
Uv pip install agent-framework --pre
uv pip install -r requirements.txt

# Run the workflow
python budget_variance_workflow.py
```
---


### Expected Console Output

```
=================================================================
  BUDGET VARIANCE WORKFLOW — START (6 AGENTS)
=================================================================

[Agent 1] MCP Data Agent — calling BudgetReportsMCPAgent v3...
[Agent 1] Retrieving department-submitted narrative reports...
[Agent 1] Done. Retrieved department narratives.
...

[Agent 2] Web Search Agent — calling WebSearchBudgetsAgent v14...
[Agent 2] Searching for economic validation data...
[Agent 2] Done. Retrieved economic context.
...

[Agent 3] Code Interpreter Agent — calling BudgetVarianceCodeIntAgent v4...
[Agent 3] Analyzing official CSV files and reconciling against claims...
[Agent 3] Done. Completed reconciliation analysis.
...

[Agent 4] Foundry IQ Policy Agent — calling BudgetPolicyAgent v1...
[Agent 4] Querying Azure AI Search for policy guidance...
[Agent 4] Done. Retrieved policy guidance.
...

[Agent 5] Summary Agent — synthesizing all outputs...
[Agent 5] Generating executive Markdown report...
[Agent 5] Converting to Word document...
[Agent 5] Done. Report saved to output_examples/budget_variance_report_*.md

[Agent 6] Outlook Mail Agent — calling BudgetWorkIQMailAgent v7...
[Agent 6] Sending email to your-email@example.com...
[Agent 6] Done. Email sent successfully.

=================================================================
  WORKFLOW COMPLETE
=================================================================
Results saved to: output_examples/
```

### Execution Time

Typical runtime: **2-4 minutes** (depends on agent response times)

---

### Sample Report Structure

The generated report includes:

1. **Executive Summary**
   - Overall variance position (total AED and %)
   - Number of CRITICAL/SIGNIFICANT departments
   - Key compliance issues
   - Top recommendations

2. **Department Variance Table**
   ```
   | Dept | Name | Approved | Actual | Variance | % | Status |
   |------|------|----------|--------|----------|---|--------|
   | IT   | ... | 4.2M     | 4.39M  | +190K    |+4.5%| ✅ OK |
   | FIN  | ... | 1.75M    | 1.95M  | +200K    |+11%| 🔶 SIG |
   ```

3. **Economic Context**
   - Validation of department claims (from Agent 2)
   - Sector trends (cloud costs, inflation, etc.)

4. **Detailed Analysis** (for SIGNIFICANT/CRITICAL departments)
   - Department claims vs. official data
   - Credibility assessment
   - Policy compliance status
   - Required actions with deadlines

5. **Recommendations**
   - Approve/reject with rationale
   - Remediation conditions
   - Future planning guidance

**View the full example:** [`output_examples/budget_variance_report_20260330_161539.md`](output_examples/budget_variance_report_20260330_161539.md)

---

## 📁 Project Structure

```
digital_transformation_demo/
├── README.md                          # This file
├── budget_variance_workflow.py        # Main orchestration script
├── budget-reports-mcp-server.py       # MCP server (deployed to ACA)
├── Dockerfile                         # Container image for MCP server
├── requirements.txt                   # Python dependencies
├── .env                               # Environment variables (create this)
│
├── deploy-to-aca.ps1                  # Azure Container Apps deployment
├── test-mcp-endpoint.ps1              # MCP server testing script
├── preflight-check.ps1                # Pre-deployment validation
│
├── data/                              # Input data files
│   ├── approved_budgets.csv           # Official approved budgets
│   ├── historical_actuals.csv         # Official spending data
│   ├── department_metadata.json       # Department reference data
│   ├── variance_policy.json           # Policy thresholds
│   │
│   ├── department_reports/            # Department narrative reports
│   │   ├── IT_Q1_2026_variance_report.md
│   │   ├── HR_Q1_2026_variance_report.md
│   │   └── INF_Q1_2026_variance_report.md
│   │
│   └── foundry_iq_docs/               # Policy documents for AI Search
│       ├── ADGA_Financial_Management_Act_2024.md
│       ├── IT_Technology_Spending_Guidelines_2026.md
│       └── Public_Sector_Procurement_Guidelines_2026.md
│
├── prompts/                           # Agent instructions
│   ├── agent1_mcp_data.txt
│   ├── agent2_web_search.txt
│   ├── agent3_code_interpreter.txt
│   ├── agent4_foundry_iq.txt
│   ├── agent5_summary.txt
│   └── agent6_outlook.txt
│
└── output_examples/                   # Sample workflow outputs
    ├── budget_variance_report_20260330_161539.md
    └── budget_variance_report_20260330_161539.docx
```

---

# Microsoft Weekly Intelligence Brief Workflow

> A **17-agent sequential pipeline** that automatically gathers, validates, analyses, and prioritises Microsoft-related news each week, then generates and emails a leadership-ready HTML intelligence brief with insights, UAE impact, and sales positioning.

---

## Overview

`ms_intelligence_workflow.py` implements a weekly newsletter workflow for Microsoft UAE leadership. It collects news from Microsoft-first-party RSS feeds, Microsoft Learn, and three web search providers, then processes the articles through a sequential enrichment pipeline before rendering a polished HTML email and delivering it via Outlook.

### Key features

- **17 sequential agents** — each agent consumes the prior step's structured JSON output
- **Three agent types** in one workflow: Foundry Agent Service, Responses API, and MAF Anthropic provider
- **Two custom MCP servers** for RSS and Microsoft Learn data retrieval
- **Intermediate checkpoints** — every agent output saved to `output/` for debugging
- **Strict JSON handoffs** — all inter-agent contracts are validated JSON
- **Outlook-compatible HTML** — rendered by Claude via MAF Anthropic provider

---

## The 17-Agent Pipeline

| # | Agent | Type | Tool / Provider |
|---|-------|------|-----------------|
| 1 | DateIntelligenceAgent | Foundry Agent Service | — |
| 2 | MicrosoftSourceAgent | Foundry Agent Service | MCP: ms-news-mcp-server |
| 3 | MicrosoftLearnAgent | Foundry Agent Service | MCP: ms-learn-mcp-server |
| 4 | TavilySearchAgent | Foundry Agent Service | Tavily |
| 5 | BingSearchAgent | Foundry Agent Service | Bing Grounding |
| 6 | SerpAPIAgent | Foundry Agent Service | SerpAPI |
| 7 | DeduplicationAgent | Foundry Agent Service | — |
| 8 | ValidationAgent | Foundry Agent Service | — |
| 9 | TopicIntelligenceAgent | Foundry Agent Service | — |
| 10 | MicrosoftMessagingAgent | Foundry Agent Service | — |
| 11 | UAEImpactAgent | Foundry Agent Service | — |
| 12 | SalesPositioningAgent | Foundry Agent Service | — |
| 13 | PriorityScoringAgent | Foundry Agent Service | — |
| 14 | NewsletterCompositionAgent | Foundry Agent Service | — |
| 15 | MediaEnrichmentAgent | **Responses API** | — |
| 16 | HTMLRenderingAgent | **MAF Anthropic provider** | Anthropic Claude |
| 17 | EmailDeliveryWorkIQAgent | Foundry Agent Service | Work IQ / Outlook |

### Agent instantiation pattern

**Foundry agents (15 agents)** — loaded by name from `.env` via `agent_reference`:
```python
response = self.openai_client.responses.create(
    input=[{"role": "user", "content": query}],
    extra_body={
        "agent_reference": {
            "name": os.getenv("AGENT_NAME"),
            "version": os.getenv("AGENT_VERSION", "1"),
            "type": "agent_reference",
        }
    },
)
```

**MediaEnrichmentAgent (Agent 15)** — Responses API with local instructions:
```python
agent = Agent(client=self.responses_client, instructions=MEDIA_ENRICHMENT_INSTRUCTIONS)
result = await agent.run(query)
```

**HTMLRenderingAgent (Agent 16)** — MAF Anthropic provider:
```python
agent = AnthropicClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6"),
).as_agent(instructions=HTML_RENDERING_INSTRUCTIONS)
result = await agent.run(query)
```

---

## Data Flow

```
Trigger
  │
  ▼
[1] DateIntelligenceAgent ──────────────────────────────────────────────────────
    Output: { start_date, end_date, interval_label }
  │
  ├──▶ [2] MicrosoftSourceAgent (MCP → RSS feeds)
  ├──▶ [3] MicrosoftLearnAgent  (MCP → Learn docs)
  ├──▶ [4] TavilySearchAgent   (Tavily)
  ├──▶ [5] BingSearchAgent     (Bing Grounding)
  └──▶ [6] SerpAPIAgent        (SerpAPI)
       Each: Output { articles: [...] }
  │
  ▼  [merge all articles]
[7] DeduplicationAgent ─── Output: { topics: [{ topic, articles }] }
  │
  ▼
[8] ValidationAgent ─────── Output: { validated_topics: [...] }
  │
  ▼
[9] TopicIntelligenceAgent ─ Output: { insights: [{ topic, summary, category }] }
  │
  ▼
[10] MicrosoftMessagingAgent ─ Output: { messaging: [{ topic, message }] }
  │
  ▼
[11] UAEImpactAgent ─────────── Output: { uae_impact: [{ topic, impact, tier }] }
  │
  ▼
[12] SalesPositioningAgent ──── Output: { sales_guidance: [{ topic, approach }] }
  │
  ▼
[13] PriorityScoringAgent ───── Output: { prioritized_topics: [{ topic, priority, score }] }
  │
  ▼
[14] NewsletterCompositionAgent ─ Output: { newsletter_sections: { title, executive_summary, topics } }
  │
  ▼
[15] MediaEnrichmentAgent (Responses API) ─ Output: { topics_with_images: [...] }
  │
  ▼
[16] HTMLRenderingAgent (Anthropic MAF) ─── Output: <HTML string>
  │
  ▼
[17] EmailDeliveryWorkIQAgent ─────────────  Output: delivery confirmation JSON
                                             Email sent to NEWSLETTER_RECIPIENT_EMAIL
```

---

## File Structure

```
maf_sequential_workflow/
│
├── ms_intelligence_workflow.py    # Main 17-agent orchestration script
├── ms-news-mcp-server.py          # RSS MCP server (Azure Blog, MS Blog, Tech Community)
├── ms-learn-mcp-server.py         # Microsoft Learn MCP server
│
├── prompts/                       # Agent system prompts
│   ├── agent01_date_intelligence.txt
│   ├── agent02_microsoft_source.txt
│   ├── agent03_microsoft_learn.txt
│   ├── agent04_tavily_search.txt
│   ├── agent05_bing_search.txt
│   ├── agent06_serpapi.txt
│   ├── agent07_deduplication.txt
│   ├── agent08_validation.txt
│   ├── agent09_topic_intelligence.txt
│   ├── agent10_microsoft_messaging.txt
│   ├── agent11_uae_impact.txt
│   ├── agent12_sales_positioning.txt
│   ├── agent13_priority_scoring.txt
│   ├── agent14_newsletter_composition.txt
│   ├── agent15_media_enrichment.txt   ← Responses API system prompt
│   ├── agent16_html_rendering.txt     ← Anthropic MAF system prompt
│   └── agent17_email_delivery.txt
│
└── output/                        # Generated newsletter HTML + checkpoints
    ├── checkpoint_01_DateIntelligence.json
    ├── ...
    ├── checkpoint_17_EmailDelivery.json
    └── ms_intelligence_brief_YYYYMMDD_HHMMSS.html
```

---

## Setup

### Prerequisites

1. **Azure AI Foundry Hub + Project** with Agent Service enabled
2. **15 Foundry agents** deployed — names must match `.env` values
3. **2 MCP servers** deployed to Azure Container Apps (ms-news-mcp-server, ms-learn-mcp-server)
4. **Anthropic API key** for HTMLRenderingAgent
5. **Microsoft 365** Outlook connection configured for EmailDeliveryWorkIQAgent

### Step 1: Deploy MCP servers

Deploy `ms-news-mcp-server.py` and `ms-learn-mcp-server.py` to Azure Container Apps using the same pattern as the budget MCP server.

Update `.env` with the deployed endpoints:
```
MS_NEWS_MCP_SERVER_URL=https://ms-news-mcp-server.<id>.eastus.azurecontainerapps.io/mcp
MS_LEARN_MCP_SERVER_URL=https://ms-learn-mcp-server.<id>.eastus.azurecontainerapps.io/mcp
```

### Step 2: Create Foundry agents

Create **15 agents** in Azure AI Foundry. For each agent:
1. Use the exact name from `.envsample` (e.g., `DateIntelligenceAgent`)
2. Copy the matching prompt from `prompts/agent0N_*.txt` as the system instructions
3. Configure the required tool (MCP endpoint, Bing Grounding, Tavily, SerpAPI, Work IQ as appropriate)
4. Set the model (recommend `gpt-5-mini` for analysis agents, `gpt-5` for composition agents)

| Agent | Tool |
|-------|------|
| MicrosoftSourceAgent | MCP → MS_NEWS_MCP_SERVER_URL |
| MicrosoftLearnAgent | MCP → MS_LEARN_MCP_SERVER_URL |
| TavilySearchAgent | Tavily search |
| BingSearchAgent | Bing Grounding |
| SerpAPIAgent | SerpAPI |
| EmailDeliveryWorkIQAgent | Microsoft 365 / Work IQ (Outlook) |
| All others | No tool required |

### Step 3: Configure environment

Copy `.envsample` to `.env` and fill in all values:

```env
AZURE_AI_PROJECT_ENDPOINT=https://your-foundry-project.services.ai.azure.com/api/projects/...
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-mini
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-6
NEWSLETTER_RECIPIENT_EMAIL=you@microsoft.com
# ... all 15 agent name variables
```

### Step 4: Install dependencies

```powershell
uv venv venv
venv\Scripts\activate
uv pip install agent-framework --pre
uv pip install -r requirements.txt
```

### Step 5: Run the workflow

```powershell
azd auth login
python ms_intelligence_workflow.py
```

---

## Environment Variables — Intelligence Brief Workflow

| Variable | Description |
|----------|-------------|
| `NEWSLETTER_RECIPIENT_EMAIL` | Email address to deliver the brief to |
| `MS_NEWS_MCP_SERVER_URL` | Deployed ms-news-mcp-server ACA endpoint |
| `MS_LEARN_MCP_SERVER_URL` | Deployed ms-learn-mcp-server ACA endpoint |
| `ANTHROPIC_API_KEY` | Anthropic API key for HTMLRenderingAgent |
| `ANTHROPIC_MODEL` | Anthropic model ID (default: `claude-opus-4-6`) |
| `DATE_INTELLIGENCE_AGENT_NAME` | Foundry agent name for Agent 1 |
| `MICROSOFT_SOURCE_AGENT_NAME` | Foundry agent name for Agent 2 |
| `MICROSOFT_LEARN_AGENT_NAME` | Foundry agent name for Agent 3 |
| `TAVILY_SEARCH_AGENT_NAME` | Foundry agent name for Agent 4 |
| `BING_SEARCH_AGENT_NAME` | Foundry agent name for Agent 5 |
| `SERPAPI_AGENT_NAME` | Foundry agent name for Agent 6 |
| `DEDUPLICATION_AGENT_NAME` | Foundry agent name for Agent 7 |
| `VALIDATION_AGENT_NAME` | Foundry agent name for Agent 8 |
| `TOPIC_INTELLIGENCE_AGENT_NAME` | Foundry agent name for Agent 9 |
| `MICROSOFT_MESSAGING_AGENT_NAME` | Foundry agent name for Agent 10 |
| `UAE_IMPACT_AGENT_NAME` | Foundry agent name for Agent 11 |
| `SALES_POSITIONING_AGENT_NAME` | Foundry agent name for Agent 12 |
| `PRIORITY_SCORING_AGENT_NAME` | Foundry agent name for Agent 13 |
| `NEWSLETTER_COMPOSITION_AGENT_NAME` | Foundry agent name for Agent 14 |
| `EMAIL_DELIVERY_WORKIQ_AGENT_NAME` | Foundry agent name for Agent 17 |

---

## HTML Output

The generated HTML newsletter (`output/ms_intelligence_brief_*.html`) includes:
- Dark navy header with title and week label
- Executive summary section (3–4 sentences synthesising the week's key themes)
- Per-topic cards with:
  - Priority badge (High = red, Medium = orange, Low = green)
  - Category badge (blue)
  - 2–3 sentence summary
  - Microsoft platform message (blue accent border)
  - UAE impact assessment + relevance tier (green accent border)
  - Seller guidance + target audience (orange accent border)
  - Source article links with date and publication name
  - Image (where available)
- Professional footer

The output is Outlook-compatible: table-based layout, inline styles only, no JavaScript.
