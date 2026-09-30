# Architecture

Aegis AI is a set of Docker Compose services behind a single FastAPI application.

![Architecture](assets/architecture.svg)

## Services

| Service | Role |
| --- | --- |
| React UI (Vite) served by Nginx | Workbench on port 3000 |
| FastAPI | Auth, chat, conversations, documents, models, audit, reports, sandbox |
| PostgreSQL | Conversations, messages, agent runs, audit events |
| Redis | Cache |
| Qdrant | Collection `industrial_docs` with dense and sparse vectors |
| Ollama | Locally hosted language models |

## Request lifecycle

```mermaid
sequenceDiagram
    participant U as Engineer
    participant A as FastAPI
    participant P as PostgreSQL
    participant Q as Qdrant
    participant O as Ollama
    U->>A: message + conversation ID + bearer token
    A->>A: resolve user, role, clearance
    A->>P: load conversation (ownership check)
    A->>Q: hybrid search (clearance filtered)
    Q-->>A: top chunks with metadata
    A->>O: generate from evidence
    O-->>A: answer
    A->>P: save message, agent run, audit event
    A-->>U: answer + citations + reasoning trace
```

## Code map

| Path | Contents |
| --- | --- |
| `backend/app/api/v1/endpoints/` | Route handlers |
| `backend/app/services/` | Orchestration, retrieval, model routing, ingestion, reporting, egress |
| `backend/app/db/` | Models and persistence helpers |
| `backend/tests/` | Automated tests |
| `frontend/` | React app and API client |
