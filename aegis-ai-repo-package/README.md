<div align="center">

<img src="docs/assets/banner.svg" alt="Aegis AI" width="100%">

[![CI](https://github.com/AbdulRehan-7designs/Ageis-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdulRehan-7designs/Ageis-AI/actions/workflows/ci.yml)
![On-Premise](https://img.shields.io/badge/deployment-on--premise-blue)
![Local LLM](https://img.shields.io/badge/LLM-100%25%20local-purple)
![SIH 2026](https://img.shields.io/badge/SIH%202026-PS%2026117-red)

### [▶ Open the interactive deep dive](https://abdulrehan-7designs.github.io/Ageis-AI/)

Click through the architecture, retrieval pipeline, chunking, audit chain, and security view.

</div>

---

## The problem

| 📚 Too many pages | 🔒 No cloud allowed | ❓ No source, no trust |
| --- | --- | --- |
| Engineers search thousands of pages of manuals and SOPs | Restricted networks can't send documents to cloud AI | AI answers without citations can't be verified |

## The solution

```mermaid
flowchart LR
    A["👷 Question"] --> B["🔐 Role + clearance check"]
    B --> C["🔎 Hybrid search<br/>authorised documents only"]
    C --> D["🧠 Local LLM answer"]
    D --> E["📌 Citations<br/>doc · page · snippet"]
    E --> F["🧾 Hash-linked audit event"]
```

## Highlights

| | |
| --- | --- |
| 📌 **Cited answers** | Document, page, and snippet with every response |
| 🏠 **Runs locally** | Embeddings, retrieval, reranking, and LLMs are self-hosted |
| 🔐 **Clearance-aware** | Filtering at query time, verified again after reranking |
| 🧾 **Auditable** | Tamper-evident audit chain with a verify endpoint |
| 🎯 **Precise** | Meaning search plus BM25 catches tags like `P-204` |

<details>
<summary><b>🔍 How retrieval works</b></summary>

```mermaid
flowchart TB
    Q[Question] --> D[Dense: BGE-M3]
    Q --> S[Sparse: BM25]
    D --> F[RRF fusion in Qdrant]
    S --> F
    F --> C[Clearance filter]
    C --> R[Rerank: bge-reranker-v2-m3]
    R --> T[Top 5 + citations]
```

Details: [docs/rag-design.md](docs/rag-design.md)
</details>

<details>
<summary><b>🏗️ Architecture</b></summary>

<img src="docs/assets/architecture.svg" alt="Architecture" width="100%">

Details: [docs/architecture.md](docs/architecture.md)
</details>

<details>
<summary><b>🔒 Security model</b></summary>

Server-side identity and clearance, ownership checks, hash-linked audit log, egress monitoring, restricted sandbox. The egress monitor is not a firewall or proof of an air gap.

Details: [docs/security.md](docs/security.md) · [SECURITY.md](SECURITY.md)
</details>

<details>
<summary><b>🔌 API</b></summary>

Swagger at `/docs`. Full table: [docs/api.md](docs/api.md)
</details>

## Run it

```bash
git clone https://github.com/AbdulRehan-7designs/Ageis-AI.git && cd Ageis-AI
cp .env.example .env      # set private credentials
docker compose up --build
```

Workbench `localhost:3000` · API docs `localhost:8000/docs` · Health `localhost:8000/api/v1/health`

> Ollama model downloads are off by default. Provision your models first.

## Stack

![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C)
![Ollama](https://img.shields.io/badge/Ollama-000000)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

## Notes

Not a certified safety system. AI can be wrong, so verify citations and keep a human in the loop. No license is set yet.

<div align="center">

**Built by [Abdul Rehan](https://github.com/AbdulRehan-7designs)** · MJCET, Hyderabad · Smart India Hackathon 2026

</div>
