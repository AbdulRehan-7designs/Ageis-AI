STEP 12 — IMPLEMENT REAL CONVERSATION + MESSAGE PERSISTENCE

Context:
Aegis AI is an enterprise/on-prem engineering intelligence application.

STEP 10 — SECURITY/AUTHORIZATION
COMPLETE.

STEP 11 — ROUTING + SESSION RECOVERY
COMPLETE.

Do NOT redesign the UI.
Do NOT create mock conversations.
Do NOT use localStorage as the database.
Do NOT use Agent Runs as a substitute for conversation history.

The goal of this step is:

CHAT PERSISTENCE.

After this step the following must work:

LOGIN
→ /workspace/chat
→ create/use conversation
→ send message
→ receive grounded AI response
→ refresh browser
→ conversation still exists
→ navigate to Documents
→ return to Chat
→ conversation still exists
→ open the conversation
→ complete message history is restored

--------------------------------------------------
PART A — DATABASE MODEL
--------------------------------------------------

Add persistent PostgreSQL models/migrations for:

Conversation
Message

Conversation should contain at minimum:

- conversation_id
- user_id / owner
- title
- created_at
- updated_at
- status
- classification/clearance metadata if required by existing security model
- optional last_message_at

Message should contain at minimum:

- message_id
- conversation_id
- role
- content
- created_at
- sequence/order
- status if required
- agent_run_id if the message corresponds to an agent execution
- safe metadata needed to restore citations/evidence

Roles should distinguish at minimum:

USER
ASSISTANT

If the current system already uses additional message roles, preserve them.

Do not store secrets or unnecessary raw security data.

--------------------------------------------------
PART B — OWNERSHIP / AUTHORIZATION
--------------------------------------------------

Conversation ownership must be server-controlled.

A normal user can:

- create their own conversations
- list their own conversations
- read their own conversations
- add messages to their own conversations
- rename their own conversations if supported

A user must NOT be able to access another user's conversation by changing a conversation ID.

ADMIN behavior should follow the existing application authorization model.

Do not trust:

- client-supplied user_id
- client-supplied owner
- client-supplied clearance
- client-supplied role

Use get_current_user() and the existing authorization layer.

--------------------------------------------------
PART C — API ENDPOINTS
--------------------------------------------------

Create/reconcile real API endpoints.

Expected functionality:

POST
/api/v1/conversations

GET
/api/v1/conversations

GET
/api/v1/conversations/{conversation_id}

POST
/api/v1/conversations/{conversation_id}/messages

Optional if useful:

PATCH
/api/v1/conversations/{conversation_id}

DELETE
/api/v1/conversations/{conversation_id}

Do not blindly create duplicate endpoints.

First inspect the existing backend for any conversation/session/message APIs.

If an existing endpoint partially implements this functionality, extend it instead of creating a competing API.

--------------------------------------------------
PART D — CHAT CONTRACT
--------------------------------------------------

Inspect the existing chat API contract.

The previous connectivity audit identified a mismatch where the frontend sends:

- chat history
- classification_filter

while the backend ChatRequest did not properly accept/use the required conversation continuity information.

Reconcile the contract.

The source of truth for history should become:

PostgreSQL conversation/messages

NOT:

frontend React state
NOT:
client-provided arbitrary history

The frontend may send the current message and conversation ID.

The backend should load the authoritative conversation history.

Example:

Frontend:

conversation_id
message

Backend:

authenticate user
↓
authorize conversation
↓
load conversation history
↓
process current message
↓
agent/RAG pipeline
↓
persist USER message
↓
persist ASSISTANT response
↓
associate Agent Run
↓
return response

--------------------------------------------------
PART E — PRESERVE EXISTING AGENT PIPELINE
--------------------------------------------------

Do NOT rewrite the existing:

- Agent Orchestrator
- Tool Registry
- RAG
- citations
- evidence groups
- model routing
- audit chain
- HITL
- report generation

Conversation persistence should wrap around the existing chat/agent pipeline.

Expected architecture:

Conversation
    ↓
Message
    ↓
Chat API
    ↓
Agent Orchestrator
    ↓
RAG / tools / model
    ↓
Agent Run
    ↓
Assistant Message
    ↓
Evidence / citations
    ↓
Audit

Existing Agent Run persistence remains authoritative for agent execution.

Conversation persistence becomes authoritative for chat history.

Do NOT duplicate entire Agent Run records into messages.

--------------------------------------------------
PART F — STREAMING CHAT
--------------------------------------------------

The existing chat streaming implementation must continue working.

Do not break SSE/streaming merely to add persistence.

Important:

Persist the USER message when the request is accepted.

Persist the ASSISTANT message only after the response is successfully completed.

If streaming fails:

- do not create a falsely completed assistant message
- record failure safely if the existing architecture supports it
- preserve the user message
- associate the failed Agent Run where appropriate

Do not persist partial streamed output as a successful final response.

--------------------------------------------------
PART G — CITATIONS / EVIDENCE
--------------------------------------------------

Conversation restoration must preserve the information required by the existing UI to render:

- assistant response
- citations
- source references
- evidence metadata
- agent run reference
- relevant reasoning/evidence state

Do not invent evidence after reload.

If citation metadata is already persisted elsewhere, reference it rather than duplicating unnecessary data.

If the current response contains transient UI-only information, identify it explicitly.

Do not weaken classification/access controls during restoration.

--------------------------------------------------
PART H — FRONTEND CHAT STATE
--------------------------------------------------

Refactor AegisChatPanel so React state is no longer the source of truth for conversation history.

The flow should become:

Route:
    /workspace/chat

↓
load user's conversations

↓
select conversation

↓
GET conversation/messages

↓
render persisted history

↓
send new message

↓
persist through backend

↓
update UI from server response

React state can still be used for:

- loading
- streaming
- currently typed message
- temporary UI state
- selected conversation

But persistent history must come from the backend.

--------------------------------------------------
PART I — CONVERSATION LIST
--------------------------------------------------

Connect the existing chat UI to the real conversation API.

If there is already a conversation/sidebar area:

- populate it from PostgreSQL
- sort by updated_at/last_message_at
- show real titles
- show real timestamps
- show empty state when no conversations exist

Do NOT create fake sample conversations.

If the current UI has no suitable conversation list, implement only the minimum required UI without redesigning the application.

--------------------------------------------------
PART J — NEW CONVERSATION
--------------------------------------------------

Implement a real "New Conversation" action if the existing UI exposes/needs it.

Expected:

New Conversation
↓
POST /conversations
↓
database row created
↓
conversation becomes active
↓
URL/state reflects active conversation
↓
user can send first message

Do not create a fake local conversation ID.

--------------------------------------------------
PART K — URL INTEGRATION
--------------------------------------------------

Step 11 introduced real routing.

Integrate conversations with the routing model without creating conflicting navigation.

Preferred structure:

/workspace/chat
/workspace/chat/:conversationId

If this fits the existing UI architecture.

Then:

/workspace/chat
    = chat landing/new conversation state

/workspace/chat/<real-id>
    = specific persisted conversation

Refresh on:

/workspace/chat/<id>

must restore that exact conversation.

If the existing application architecture has a better equivalent, preserve consistency.

Do NOT use arbitrary client-side IDs.

--------------------------------------------------
PART L — NAVIGATION PERSISTENCE
--------------------------------------------------

Validate:

Conversation A
↓
send message
↓
Documents
↓
Chat
↓
Conversation A still visible

Then:

Conversation A
↓
Models
↓
Runs
↓
Chat
↓
Conversation A still visible

No loss of server-persisted history.

--------------------------------------------------
PART M — REFRESH TEST
--------------------------------------------------

This is the critical test.

Test exactly:

1. Login
2. Open Chat
3. Create a conversation
4. Send:

"What does the maintenance procedure say about pump vibration?"

5. Wait for grounded response.
6. Verify assistant response and citations.
7. Refresh browser.
8. Verify conversation remains.
9. Verify user message remains.
10. Verify assistant response remains.
11. Verify citations/evidence still render correctly.
12. Navigate to Documents.
13. Return to Chat.
14. Open the same conversation.
15. Verify complete history remains.

This test MUST pass before Step 12 is considered complete.

--------------------------------------------------
PART N — RESTART TEST
--------------------------------------------------

Because this is an on-prem production system, test persistence across backend restart.

Sequence:

create conversation
↓
send message
↓
restart backend/container
↓
login/session recovery
↓
open Chat
↓
conversation remains
↓
messages remain

Do not rely on process memory.

--------------------------------------------------
PART O — SECURITY TESTS
--------------------------------------------------

Add tests for:

1. Unauthenticated conversation list -> 401
2. Unauthenticated conversation read -> 401
3. User A cannot read User B conversation -> 403/404 according to existing security convention
4. User A cannot append to User B conversation
5. Client cannot change conversation owner
6. Client cannot change classification to gain access
7. ADMIN behavior follows policy
8. Existing clearance enforcement remains active
9. Conversation messages do not leak across users
10. Existing Step 10 authorization tests remain passing

--------------------------------------------------
PART P — DATA INTEGRITY
--------------------------------------------------

Add database constraints/indexes for:

- conversation owner
- conversation timestamps
- message conversation_id
- message sequence/order
- useful lookup indexes

Use a migration.

Do not modify existing production data destructively.

Existing migrations must continue to work from a clean database.

--------------------------------------------------
PART Q — AUDIT
--------------------------------------------------

Integrate conversation lifecycle with the existing audit architecture where appropriate.

Possible events:

CONVERSATION_CREATED
CONVERSATION_MESSAGE_CREATED
CONVERSATION_DELETED

Use safe metadata only.

Do not put raw sensitive document content into audit records.

Preserve the existing hash-chain audit architecture.

--------------------------------------------------
PART R — ERROR/RECOVERY BEHAVIOR
--------------------------------------------------

Handle:

conversation not found
conversation unauthorized
database failure
agent failure
stream interruption
expired JWT
403 response

Use the existing Step 10 centralized 401/403 handling.

Do not silently replace server failures with empty conversations.

Explicitly distinguish:

EMPTY
LOADING
ERROR
UNAUTHORIZED

--------------------------------------------------
PART S — DO NOT IMPLEMENT FUTURE STEPS
--------------------------------------------------

Do NOT implement:

- Assets
- Settings
- full Agent Run detail page
- sandbox redesign
- report center
- report history redesign
- JWT blacklist/revocation
- equipment graph
- Neo4j
- new AI capabilities

Only implement conversation/message persistence and the minimum UI/API integration required for it.

--------------------------------------------------
VALIDATION
--------------------------------------------------

Run:

- full backend tests
- conversation-specific tests
- security tests
- migration tests
- frontend diagnostics
- frontend production build
- Python syntax checks

Perform browser validation of:

LOGIN
↓
CHAT
↓
NEW CONVERSATION
↓
SEND MESSAGE
↓
AI RESPONSE
↓
CITATIONS
↓
REFRESH
↓
HISTORY RESTORED
↓
DOCUMENTS
↓
CHAT
↓
SAME CONVERSATION
↓
BACK/FORWARD
↓
HISTORY STILL PRESENT

Then:

BACKEND RESTART
↓
LOGIN
↓
CHAT
↓
CONVERSATION STILL PRESENT

Report:

1. Files changed
2. Database migration
3. New/reconciled APIs
4. Conversation ownership model
5. Message persistence model
6. Chat contract changes
7. Frontend changes
8. Streaming behavior
9. Citation restoration behavior
10. Security tests
11. Refresh test
12. Backend restart persistence test
13. Full test count
14. Build result
15. Remaining limitations

IMPORTANT:

Do not declare Step 12 complete if messages only survive through React state or localStorage.

The authoritative persistent source MUST be PostgreSQL