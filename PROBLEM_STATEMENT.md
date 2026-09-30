# AegisAI — Problem Statement & Build Alignment

This file is the source of truth for *why* we are building AegisAI and *how* we implement it. Do not optimize for a generic chatbot. Optimize for this SIH problem, for MRPL-style confidential industrial work, and for a system that can actually be deployed.

**Keep this file updated** when scope or model policy changes.

---

## Official problem

**Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work

**Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
**Department:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
**Category:** Software  
**Theme:** Smart Automation  
**Dataset:** Open-source models and publicly available document samples (sample scanned PDFs, sample P&IDs from open datasets). No proprietary data required.

### Background (verbatim intent)

Refineries, PSUs, defence-linked manufacturing units and government offices generate a lot of routine but sensitive knowledge work: approval notes, board presentations, engineering calculations, code for internal tools, review of scanned drawings and inspection reports.

None of this can go through cloud AI assistants because the underlying data is confidential: Piping & Instrument Diagrams, financials, vendor negotiations, unreleased designs, internal correspondence, confidential business strategies, etc.

Company policy keeps this data on premises, so people either do the work manually (no productivity gain) or they quietly paste confidential material into public tools. Open-weight large reasoning models have reached a point where a genuinely useful assistant is realistic. Nothing deployable exists today that industrial users can actually work with the way they use Claude or Codex.

### Required product (verbatim intent)

A self-hosted, **air-gapped** AI workbench running entirely on the organization's own GPU server. **Nothing leaves the premises.**

- Backend **must not be locked to one model**. Support multiple open-weight models at once.
- **Automatically pick the right model** for a given task (coding vs document summary, etc.).
- **New open-weight models must be addable later without redesigning the system.**
- The assistant must **act like an agent**: plan multi-step work, call local tools (file read/write, sandboxed code execution, spreadsheet work, internal document search), and **iterate** instead of answering once and stopping.
- **Multimodal:** scanned PDFs, handwritten notes, engineering drawings, photographs — on-device OCR and vision models.
- Output should be **real deliverables**: approval notes, PPT/Word/Excel files, working code, calculations with steps shown — not only chat replies.
- Ground answers in the organization's own manuals, SOPs and past correspondence via a **local knowledge base**. Nothing external.

### Expected solution (judging bar)

A working **local** deployment, demonstrable on a single workstation or server with a mid-range GPU (use a smaller open-weight model if 120B-class hardware is not available), that shows:

1. **Model auto-selection across at least two different task types.**
2. **An agentic task carried through end to end** — e.g. reading a scanned inspection report, extracting key findings, and drafting an approval note as a **Word file**.
3. **A coding task run and verified in a sandbox.**
4. **A multimodal task** involving image or scanned-document understanding.
5. **Proof of sovereignty:** logs or a visible network monitor showing **no external calls at any point**. That is the actual proof of the sovereign claim, not a statement of it.

---

## Project decisions (ours)

### Models

Hardware and latency come first. **Default runtime models are 3B-class Ollama models:**

| Role | Ollama tag | Status |
|------|------------|--------|
| Chat / document / reasoning | `qwen2.5:3b` | **Active** |
| Code / calculations / sandbox | `qwen2.5-coder:3b` | **Active** |
| Vision / OCR / drawings | (not pulled yet) | **Disabled until we truly need it** |

Do **not** pull 7B/14B/VL models “because the problem mentions multimodal.” Add a model only when a slice of this problem cannot be done correctly with the 3B stack. When adding a model: register it in `backend/app/core/model_catalog.json` and pull it in `backend/ollama_entrypoint.sh`. Do not hardcode model names in the orchestrator or UI.

### Build policy

- Production-ready **one slice at a time**. Each slice must leave chat, RAG, upload, and the existing UI working.
- No fake production: do not claim air-gap, RBAC, sandbox, or audit durability unless the code actually enforces it.
- Prefer local, addable registries and connectors over one-off if/else locked to a single model or vendor.
- Demo data only: public sample PDFs / open P&IDs. Never require MRPL proprietary documents.

### Implementation order (do not skip ahead into a rewrite)

1. **Model registry + auto-routing** — two task types, addable models, 3B defaults.
2. **Real sovereignty proof** (current) — egress guard on httpx, live monitor, no CDN/unpkg in the UI.
3. **Durable records** — Postgres for users/docs/audit; stop using RAM-only ledgers.
4. **Auth that can go to production** — real login, no anonymous ENGINEER in `ENVIRONMENT=production`; keep a documented demo mode for local SIH runs.
5. **Agent tools + deliverables** — file tools, sandbox that actually runs and reports, Word/Excel generation for approval notes.
6. **Multimodal** — enable a small VL/OCR model only when this slice starts; scanned inspection → findings → `.docx`.
7. **Hardening** — TLS, secrets, upload limits, isolated sandbox, backups, health that fails closed.

---

## Non-goals for the current slice

- Do not switch default models to 7B+.
- Do not rip out the existing RAG/chat UI.
- Do not implement a full IdP until slice 4.
