# Security model

> Aegis AI is not a certified safety system. This document describes intended controls, not guarantees.

## Trust boundaries

![Architecture](assets/architecture.svg)

The browser is untrusted. Identity, role, and clearance are resolved on the server for every request.

## Threats and controls

| Threat | Control | Where |
| --- | --- | --- |
| Client claims a higher clearance | Clearance resolved server-side from the authenticated user | API auth layer |
| User reads documents above their clearance | Query-time filter, then re-verification after reranking | `services/retrieval.py` |
| User reads another user's chat | Conversation ownership checks | conversations endpoints |
| Silent edit of audit history | Hash-linked events, verify endpoint | `GET /api/v1/audit/verify` |
| Data leaves the network | Egress monitor on guarded `httpx` clients can log and block | `services/` egress |
| Untrusted code execution | Restricted sandbox endpoint | sandbox endpoint |
| Wrong or hallucinated answer | Citations with document, page, snippet; human review | chat response |

## Known limits

- The egress monitor is not a firewall and not proof of an air gap. Add network controls outside the app.
- OCR and generated answers can be wrong.
- Protect `.env`, uploaded documents, model files, and generated artifacts.

Report vulnerabilities as described in [SECURITY.md](../SECURITY.md).
