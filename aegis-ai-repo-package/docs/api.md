# API reference

Interactive schema at `http://localhost:8000/docs`. All routes except login and health need `Authorization: Bearer <token>`.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | Sign in |
| POST | `/api/v1/chat` | Send a chat message |
| POST | `/api/v1/chat/stream` | Stream a response |
| GET | `/api/v1/conversations` | List accessible conversations |
| GET | `/api/v1/conversations/{id}` | Restore a conversation |
| POST | `/api/v1/document/upload` | Ingest a document |
| GET | `/api/v1/document/list` | List accessible documents |
| GET | `/api/v1/models` | Model catalog |
| GET | `/api/v1/agent-runs` | Agent runs |
| GET | `/api/v1/audit/logs` | Permitted audit events |
| GET | `/api/v1/audit/verify` | Verify audit chain |
| GET | `/api/v1/health` | Health |

## Example: chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"message":"What are the vibration limits for P-204?","history":[],"classification_filter":"INTERNAL"}'
```

Response includes `citations` (document, page, tag, snippet) and a `reasoning_trace`.
