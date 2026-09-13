> **CONFIDENTIAL** — SIH 2026 Idea Submission (Team GLITCH). For internal review and evaluation purposes only.

# AegisAI
### Sovereign Agentic AI for Secure Industrial Workflows

**Smart India Hackathon 2026**
**Problem Statement ID:** SIH26117
**Problem Statement Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work
**Theme:** Smart Automation
**PS Category:** Software
**Team Name:** GLITCH

---

## Table of Contents
1. [Overview](#overview)
2. [Problem Overview](#problem-overview)
3. [Problem Solution](#problem-solution)
4. [Core Features, by Build Phase](#core-features-by-build-phase)
5. [Innovation and Uniqueness](#innovation-and-uniqueness)
6. [Output Classification & Confidentiality Tagging](#output-classification--confidentiality-tagging)
7. [Technical Approach](#technical-approach)
8. [System Requirements](#system-requirements)
9. [Quick Start](#quick-start)
10. [Feasibility and Viability](#feasibility-and-viability)
11. [Impact and Benefits](#impact-and-benefits)
12. [Known Limitations](#known-limitations)
13. [Roadmap](#roadmap)
14. [Team](#team)
15. [Research and References](#research-and-references)
16. [License](#license)

---

## Overview

AegisAI is an on-premise, agentic AI workbench built for organizations that cannot send confidential industrial or government data to cloud AI tools. It replaces the current choice between manual work and unauthorized use of public AI tools with a secure, multi-step, multimodal AI system that runs entirely offline.

---

## Problem Overview

- Confidential industrial/government data cannot be sent to cloud AI tools.
- Employees currently face two choices: manual work or unauthorized AI use.
- Existing on-premise AI is limited to single-model chatbots.
- These tools fail at multi-step tasks: document understanding, reasoning, tool use.
- **Need:** a secure on-premise AI workbench that handles full industrial knowledge work inside the organization.
- **Key features required:** data sovereignty, multi-model orchestration, workflow automation, compliance.

---

## Problem Solution

- **Zero external dependency:** Runs entirely on-premise with zero external API calls.
- **Multimodal intelligence:** Processes industrial documents, images, drawings, and technical data.
- **Trusted RAG:** Generates citation-backed answers using verified internal knowledge.
- **Agentic automation:** Executes multi-step industrial tasks through controlled AI agents.
- **Intelligent routing:** Automatically selects the most suitable local model for each task.
- **AI safety layer:** Combines risk assessment, self-verification, sandboxing, and human approval.

---

## Core Features, by Build Phase

### 1. Foundation & Core RAG (Weeks 1–2)
- FastAPI backend in Docker
- Hybrid RAG using ChromaDB (BM25 + dense retrieval)
- PDF ingestion with page-level citations
- **Chunking strategy for technical docs** — engineering PDFs contain tables, diagrams, and multi-column layouts that naive text chunking destroys; a layout-aware or semantic chunking approach is decided early since it's costly to redo later
- **Evaluation harness** — a test set of Q&A pairs to measure retrieval precision/recall, so retrieval quality is provable rather than only demoed
- Basic React chat UI
- *Demo: Upload a PDF, get a cited, sourced answer*

### 2. Multimodal & Routing (Weeks 3–4)
- Surya OCR for scanned documents
- Qwen2-VL for parsing images/P&ID (piping & instrumentation diagrams)
- Task classifier that routes queries to the right model
- Swappable model registry (not locked to one LLM)
- *Demo: Parse a scanned P&ID drawing live*

### 3. Agentic Execution Layer (Weeks 5–6)
- LangGraph-based plan → execute → verify loop
- Docker sandbox for safe tool execution
- A 4-stage industrial risk engine that flags risky actions before execution
- Self-verification re-read pass (agent checks its own output)
- *Demo: Agent completes a multi-step task solo*

### 4. Governance & Security (Weeks 7–8)
- Role-based access control + audit ledger
- Human-in-the-loop approval UI for sensitive actions
- Network egress monitor (proves zero external calls — key for the "sovereign" claim)
- Prompt-injection guardrails
- *Demo: Prove zero external network calls, live*

### 5. Scale & Deployment (Post-selection)
- One-click Docker Compose packaging
- Multi-site/multi-plant rollout support
- Plug-in architecture for swapping open-weight models
- Pilot planned with a PSU (public sector undertaking) or defense partner
- *Demo: Deploy the same package to a second site*

**The overall pitch:** an agentic AI system built specifically for industrial/government environments where data can't leave the premises — combining document RAG, visual parsing of technical drawings, autonomous multi-step task execution, and strict governance/audit controls.

---

## Innovation and Uniqueness

| Capability | Description |
|---|---|
| No External API Calls | System operates entirely offline; provable via UI |
| Iterative Task Execution | Agent plans, executes, uses tools, verifies, and retries until task completion |
| Downloadable File Outputs | Generates .docx, .pptx, .xlsx, .py files — not just chat replies |
| Critical Step Approval | Agent pauses for human approval before finalizing critical tasks |
| Offline OCR & Vision | Scanned PDFs and images processed offline for structured data |
| Automatic Model Selection | AI chooses the best model (code, vision, text, reasoning) per query |
| Auditable Source Attribution | Every answer linked to exact document and page number |
| AI Safety Checks | Output undergoes safety, sanity, and regulatory checks before delivery |
| AI Output Validation | Agent re-reads and cross-checks its own output for hallucinations |
| Easy Model Updates | New open-weight models can be added without code changes |

---

## Output Classification & Confidentiality Tagging

Every answer, citation, and generated document carries a classification tag inherited from the RBAC tag on its source material — this is not cosmetic, it is enforced and auditable.

| Tag | Meaning | Behavior |
|---|---|---|
| `CONFIDENTIAL` | Sourced from restricted-access documents | Requires HITL approval before export; watermarked in exported .docx/.pptx headers & footers |
| `RESTRICTED` | Sourced from role-limited internal documents | Visible only to users with matching RBAC role; logged in audit ledger |
| `INTERNAL` | Sourced from general internal knowledge base | Standard citation display, no export restriction |

- Tags appear inline in the chat UI next to each citation (document + page number).
- Exported deliverables (Word, PPT, Excel) inherit the highest classification level among all cited sources.
- Every tag assignment and export event is written to the audit ledger with timestamp, user, and document hash — supporting the CERT-In / NCIIPC compliance claims in Feasibility & Viability.

---

## Technical Approach

### Methodology
1. **Requirement Analysis** — Gather industrial needs, security rules, and user scenarios.
2. **System Architecture Design** — Define air-gapped architecture with model registry & router.
3. **Infrastructure & Sandbox Setup** — Deploy GPU server, Ollama, ChromaDB & Docker Code Sandbox.
4. **Backend Development** — Build FastAPI backend, task classifier, and tool APIs.
5. **Workbench UI Development** — Create React UI with chat, network monitor & HITL panel.
6. **Agent & Sandbox Tool Integration** — Integrate LangGraph agent loop with Docker Sandbox Execution tool.
7. **Citation-Level RAG** — Build ChromaDB RAG with page citations & hybrid search.
8. **Security Hardening** — Apply industrial risk engine, prompt guard, and audit log.
9. **Sandbox Validation & Testing** — Test code execution in isolated sandbox & verify outputs.
10. **Sovereign Deployment** — Deploy via Docker Compose on a single GPU workstation.

### Flow Chart
1. Input: text prompt or uploaded document
2. User submits query or uploads file (PDF, image, scanned doc, code)
3. Task classifier detects task type (keyword + embedding similarity routing)
4. Model router selects best local model (Code → Qwen-Coder | Vision → Qwen-VL | Text → Qwen2.5)
5. Agent breaks task into sub-steps with tools
6. LangGraph agent plans multi-step workflow
7. Agent calls local tools: RAG Search, OCR, Vision, Code Sandbox, Calculator, Doc Generator (all on-premise)
8. Self-verification: agent checks answer quality
9. Industrial risk engine validates & assesses risk level
10. Passes self-verification & risk engine check?
    - **No** → Agent retries or flags risk warning to user
    - **Yes** → Human-in-the-loop approval gate
11. Agent pauses, user reviews and approves output
12. Document generator produces deliverable (Word, PPT, Excel, code, etc.)
13. Inline citations added (page number + exact source reference)
14. Network monitor logs zero external calls — sovereignty proof, no packets leave the server
15. User receives final deliverable with inline citations

### Tech Stack
- **Frontend:** React + Vite (Vanilla CSS)
- **Backend:** FastAPI (Python)
- **Code Sandbox:** Docker, WebSocket
- **OS Support:** Ubuntu 22.04 / Windows 11
- **Document Generation:** python-docx, python-pptx, openpyxl
- **Agent Framework:** LangGraph (LangChain)
- **Model Runner:** Ollama (GPU)
- **Vector Store:** ChromaDB (local)
- **OCR:** Surya (on-device)
- **Deployment:** Docker Compose, GPU (NVIDIA)
- **Logging & Security:** structlog, prompt-injection guard

---

## System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU | 12GB VRAM (e.g., RTX 3060) | 24GB VRAM (e.g., RTX 4090) |
| RAM | 16GB | 32GB |
| Storage | 50GB free (models + vector store) | 150GB SSD |
| OS | Ubuntu 22.04 or Windows 11 | Ubuntu 22.04 |
| Runtime | Docker, Docker Compose | Docker, Docker Compose, NVIDIA Container Toolkit |

## Quick Start

```bash
git clone <repo-url>
cd ageis-ai
docker compose up --build
# Access the workbench at http://localhost:3000
```

Default deployment runs fully offline after initial model pull — no external API keys required.

---

## Feasibility and Viability

| Dimension | Analysis |
|---|---|
| **Technical** | Achievable on a mid-range GPU workstation using Ollama, LangGraph, FastAPI, and ChromaDB. |
| **Economical** | Zero recurring API costs; low total cost of ownership running open-weight 7B models locally on existing PSU hardware. |
| **Social** | Boosts productivity for PSU and defense engineers while ensuring 100% data confidentiality. |
| **Legal & Compliance** | Enforces local data processing, no external API dependency; complies with PSU/defense air-gap policies, IT Act, and CERT-In guidelines. |
| **Operational** | Simple web interface, automated model selection, and human-in-the-loop approval enable adoption without deep AI expertise. |
| **Security** | Isolated Docker sandbox, local RBAC, on-device OCR, real-time network egress monitoring. |

### Potential Challenges and Risks → Mitigation Strategies

| Challenge | Strategy |
|---|---|
| Running multimodal and coding models on limited VRAM hardware | **Model Auto-Routing** — route tasks to single 7B quantized models via Ollama for efficient use on 12GB VRAM |
| Extracting text from dense P&ID drawings, handwritten notes, scanned PDFs | **Hybrid OCR & Vision** — Surya OCR combined with Qwen2-VL for accurate text and diagram parsing |
| Risk of AI generating incorrect engineering figures or formulas | **Industrial Risk Engine** — agent self-verification & rule-based sanity checks before delivery |
| Malicious inputs attempting to bypass safety guardrails or access unauthorized documents | **Strict Guardrail Sanitizer** — regex input filtering, RBAC document tags, real-time network monitoring |

---

## Impact and Benefits

### Unique Features
- **Provable Air-Gapped Sovereignty** — real-time network monitor proves zero external packet transmission
- **Multi-Model Task Auto-Routing** — hybrid classifier selects the optimal open-weight model per task
- **Plan-Execute-Verify Agentic Loop** — autonomous multi-step execution using Docker Sandbox, RAG, and OCR tools
- **Citation-Level RAG Grounding** — every response grounded with exact document and page-level attribution
- **Industrial Risk Engine & HITL** — output safety validation with mandatory human-in-the-loop approval gates

### Impacts
- **Zero-Trust Air-Gapped OPSEC** — confidential data stays on-premise, verified via network monitoring
- **Knowledge Workflow Acceleration** — automates document parsing, SOP cross-referencing, calculations, and report generation
- **Citation-Level Grounding** — every answer/recommendation linked to its exact source document and page
- **Multimodal Industrial Perception** — processes scanned PDFs, handwritten logs, equipment images, and engineering drawings offline

### Benefits
- **Eliminate Cloud AI Costs** — runs open-weight models locally, removing recurring API costs and vendor dependency
- **Security & Compliance** — combines air-gapped deployment, access controls, encryption, and audit trails
- **Future-Proof Model Portability** — offline model registry and intelligent routing allow easy addition of new open-weight models
- **Turnkey Deployment** — Docker-based deployment with isolated sandboxes for safe agent tool execution

---

## Known Limitations

- Model quality is capped by 7B-class open-weight models to fit consumer/mid-range GPU VRAM — larger reasoning tasks may need cloud-scale models, which this system deliberately excludes for sovereignty.
- OCR accuracy on heavily degraded scans or handwritten notes is lower than on clean digital PDFs.
- Multi-site deployment (Phase 5) has not yet been validated beyond a single workstation.
- Human-in-the-loop approval adds latency to critical-path tasks by design — a deliberate safety trade-off, not a bug.

## Roadmap

See the phased development roadmap (Foundation & Core RAG → Multimodal & Routing → Agentic Execution → Governance & Security → Scale & Deployment) for build timeline, demo checkpoints, and post-selection vision.

## Team

**Team Name:** GLITCH
*(Add member names and roles here)*

---

## Research and References

- **Qwen2.5-Coder & Qwen2-VL Models** — Open-weight 7B foundation models delivering SOTA code generation and multimodal parsing of scanned PDFs and P&ID engineering diagrams.
  Link: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct

- **ReAct & Self-Refine Agent Architecture** — Framework combining step-by-step reasoning with tool execution, featuring autonomous self-verification loops before output delivery.
  Link: https://arxiv.org/abs/2303.17651

- **LangGraph & ChromaDB RAG Framework** — Stateful graph orchestrator enabling Human-in-the-Loop review paired with a zero-dependency, local vector store for page-level PDF citations.
  Link: https://www.sciencedirect.com/science/article/pii/S0957417426000746

- **Hybrid BM25 & Dense Vector Retrieval** — Combines keyword search with semantic embeddings (Sentence-BERT) to guarantee exact document citation matching for technical SOPs.
  Link: https://doi.org/10.1145/3471158.3472233

- **CERT-In & NCIIPC Cybersecurity Guidance** — Government cybersecurity standards mandating 100% on-premise data containment and zero outbound network telemetry for Critical Information Infrastructure.
  Link: https://www.cert-in.org.in/s2cMainServlet?pageid=GUIDLNVIEW02&refcode=CISG-2023-01

---

## License

Proprietary — Smart India Hackathon 2026 submission by Team GLITCH. Not licensed for external use or distribution pending evaluation outcome.
