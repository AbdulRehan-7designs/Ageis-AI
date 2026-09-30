# Aegis AI Frontend V1 — Quick Start Guide

## Start the Stack

### 1. Backend

```bash
cd backend
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

Expected output:
```
➜ Local:   http://localhost:5173/
```

Open browser to **http://localhost:5173**

---

## Login

**Username:** `test_operator`  
**Password:** `password`

Or use any username with clearance tags from the backend.

---

## Navigation

### Sidebar (Left)

**WORKSPACE**
- **Home** — Dashboard with system status, recent activity
- **Chat** — Real-time chat with citations, evidence, agent trace
- **Documents** — Search and filter technical documents
- **Assets** — Asset explorer (placeholder for now)

**INTELLIGENCE**
- **Models** — Available models and task routing
- **Agent Runs** — (Embedded in chat traces for now)

**GOVERNANCE**
- **Audit Logs** — Immutable audit trail
- **Security** — Clearance, RBAC, egress status

**SYSTEM**
- **Settings** — (Coming soon)

### Top Header (Right)

- **Global Search** (top right)
- **System Status Badge** (green = healthy)
- **User Profile** (bottom left of sidebar)
- **Sign Out** (bottom left)

---

## Pages

### Home Dashboard

**Quick Actions**
- Ask Aegis
- Search Documents
- Investigate Asset
- View Agent Runs

**Recent Activity**
- Last 5 audit entries

**System Status**
- Real health check from backend
- Shows API, Retrieval, Vector DB, Audit status

**Authorized Documents**
- First 5 documents you can access

### Chat Workspace

1. Type a question: *"What is the maintenance procedure for P-204?"*
2. Click **Send**
3. See real response with:
   - **Diagnosis** (main answer)
   - **Citations** (source documents)
   - **Evidence** (supporting snippets)
   - **Agent Trace** (6-step reasoning pipeline)
   - **Model Used** (which model answered)

**Right Panel** (Context)
- Click a citation to view full source
- See related assets and tags
- Verify classification level

### Documents Page

- **Search:** Full-text search across indexed documents
- **Filters:** Document type, asset, classification, tags
- **View:** Click a document to open in evidence viewer

### Models Page

- **Auto Router:** Default model selector (picks chat vs. coder)
- **Models List:** Shows available local models
  - Display name
  - Task types (chat, document_summary, code)
  - Provider (Ollama)
  - VRAM hint
  - Enabled status

### Audit Logs Page

- **Chain Verification:** ✅ (valid) or ⚠️ (broken)
- **Entries:** Timestamp, event type, user, status
- **Search/Filter:** By event type or username
- **Details:** Click row to see full entry

### Security Page

- **Clearance Level:** Your authorization level
- **RBAC:** Verified (enforced by backend)
- **External Sources:** Allowed or blocked
- **Audit Chain:** Integrity status

---

## Test Real Integration

### Run End-to-End Tests

```bash
cd frontend
node test-e2e.js
```

This validates:
- ✅ Login
- ✅ Model fetch
- ✅ Chat response
- ✅ Citations render
- ✅ Evidence blocks render
- ✅ Reasoning trace renders
- ✅ Audit logs fetch
- ✅ Audit chain verification

Expected: **All tests passed** ✅

---

## Common Workflows

### Ask About Equipment

1. Go to **Chat**
2. Type: *"What maintenance procedures apply to pump P-204?"*
3. See:
   - Answer from real backend
   - Citations to SOP documents
   - Evidence blocks with specific procedures
   - Reasoning trace showing search + model selection
   - Model info (e.g., Qwen 2.5 3B)

### Search for a Document

1. Go to **Documents**
2. Type: *"SOP-017"* in search box
3. Filter by: Document Type = *SOP*
4. Click document to open evidence viewer
5. See: Document name, page number, asset tags, classification

### Review Audit Trail

1. Go to **Audit Logs**
2. See all operations by timestamp
3. Verify **Chain Integrity** badge (green = valid)
4. Click entry to see details: who did what, when, on what asset

### Check System Health

1. Go to **Home**
2. Look at **System Status** cards:
   - **API:** Green = backend running
   - **Retrieval:** Green = RAG/vector DB working
   - **Audit:** Green = audit chain valid

---

## Troubleshooting

### "Unable to connect to Aegis services"

**Backend is not running.**

```bash
cd backend
python main.py
```

### "Login failed"

Check:
- Backend is running
- Username is correct
- Password is correct (default: `password`)

### "No models available"

**Backend model registry is empty or misconfigured.**

Check backend logs:
```bash
# In backend terminal, look for:
INFO: 3 models registered
```

### "Chat returns empty response"

**RAG/vector DB might be offline.**

Check **Home > System Status**:
- ✅ Retrieval = green
- ✅ Vector DB = green

If red, restart backend.

### "Audit chain is broken"

**Audit integrity compromised.**

This is a real security concern. Check:
- Log file: `backend/audit.log`
- Verify no entries were deleted or modified

---

## API Endpoints (Reference)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/login` | POST | Authenticate | No |
| `/health` | GET | System status | No |
| `/models` | GET | Available models | No |
| `/chat` | POST | Chat (blocking) | Yes |
| `/chat/stream` | POST | Chat (streaming) | Yes |
| `/document/list` | GET | Search documents | Yes |
| `/audit/logs` | GET | Audit entries | Yes |
| `/audit/verify` | GET | Chain verification | Yes |
| `/egress` | GET | External sources | No |

---

## Design Colors

For custom development, reference these colors:

```css
--bg-primary: #FAFAF9      /* Page background */
--bg-secondary: #F7F8FA    /* Card background */
--surface: #FFFFFF          /* Surfaces */
--text-primary: #252525     /* Main text */
--text-secondary: #6B7280   /* Secondary text */
--border: #E5E7EB           /* Borders */
--accent-primary: #8DB9E8   /* Main accent (blue) */
--accent-secondary: #B7D5F2 /* Light accent */
--dark-slate: #374151       /* Dark variant */
```

---

## Performance Tips

- **Chat:** First response ~2-3 seconds (planning + retrieval + generation)
- **Document search:** <500ms
- **Audit logs:** <200ms
- **Page navigation:** Instant

If slow:
- Check backend CPU usage
- Check network latency
- Verify vector DB is responding

---

## Keyboard Shortcuts

- **Ctrl+L** — Focus search
- **Ctrl+K** — Open command palette (coming soon)
- **Escape** — Close modals
- **Enter** — Send chat message

---

## Next Steps

1. **Explore Chat**
   - Send several engineering queries
   - Verify citations and evidence appear
   - Check audit trail records the interaction

2. **Test Documents**
   - Search for specific SOPs or manuals
   - Filter by asset or classification
   - Verify only authorized documents appear

3. **Review Security**
   - Check your clearance level
   - Verify RBAC enforces access control
   - Confirm audit chain is valid

4. **Check Models**
   - See which models are available
   - Understand task routing (auto selector)
   - Note provider (Ollama, local)

---

## Feedback

After testing, note:

- [ ] UI is intuitive
- [ ] Responses are accurate
- [ ] Citations are relevant
- [ ] Evidence is helpful
- [ ] Performance is acceptable
- [ ] Security posture is clear

Share feedback with the team.

---

## Support

For issues:

1. Check backend logs: `cd backend && tail -f main.log`
2. Check frontend console: F12 → Console
3. Run end-to-end tests: `node test-e2e.js`
4. Restart both services if stuck

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-17  
**Status:** Ready for testing ✅
