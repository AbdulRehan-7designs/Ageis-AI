============================================================
STATUS (READ THIS FIRST) — 2026-09-20
============================================================

This file is the **RAG/evidence target architecture**, not a claim that Aegis already
does all of it. Product / SIH / 3B model policy lives in `PROBLEM_STATEMENT.md`.
If the two conflict (cloud APIs, 7B models, rewrite-the-app), follow PROBLEM_STATEMENT.

Build incrementally. Do not implement all 54 sections in one pass.

Implemented enough to use today
- PDF upload → PyMuPDF extract → layout-ish chunks → Qdrant **dense + sparse/BM25**
- Identifier payload (`equipment_tags`) + identifier-first fusion for tags like P-204 / PSV-204
- Local embeddings (`BAAI/bge-small-en-v1.5`) and optional local reranker
- Clearance filter on retrieve (before the LLM sees chunks)
- Query router labels intent/strategy and extracts identifiers
- Citation payload (doc, page, tag, bbox fields, stored filename)
- **Real PDF viewer + bbox highlight** on citation click (no fake P&ID canvas)
- Model catalog + auto chat vs coder (3B Ollama). Egress guard on httpx.

Designed here but NOT real yet (do not demo as done)
- Iterative multi-hop retrieval loop
- OCR, DOCX/XLSX/CSV/image ingestion
- P&ID graph / connected-to spatial intelligence
- Revision-aware conflict resolution
- Claim-level citations, evidence verification agent
- Durable provenance DB (Qdrant + files only; audit is still in RAM)
- Production RBAC (demo JWT / anonymous ENGINEER fallback still exists)

Next after these RAG slices
- Durable Postgres records (audit/docs/users)
- Agent deliverables (Word approval note)

============================================================

You are the principal AI architect and senior full-stack engineer responsible for building the next-generation RAG platform for Aegis AI.

Aegis AI is a sovereign, on-premise engineering and enterprise AI platform.

Your task is to build a production-grade:

                    AGENTIC HYBRID RAG SYSTEM

combined with:

- document intelligence
- engineering drawing intelligence
- P&ID intelligence
- semantic search
- keyword/BM25 search
- vector search
- metadata filtering
- reranking
- query decomposition
- agentic retrieval
- multi-hop retrieval
- graph-aware retrieval
- citation/provenance tracking
- evidence visualization
- PDF viewer
- engineering drawing viewer
- OCR
- table extraction
- document comparison
- source verification
- RBAC
- auditability
- sovereign/on-premise deployment

This is NOT a toy chatbot.

This is NOT a simple:

PDF → chunks → embeddings → vector DB → LLM

pipeline.

Build Aegis as an evidence-first enterprise/engineering intelligence system.

============================================================
0. FIRST RULE — INSPECT BEFORE MODIFYING
============================================================

Before writing code:

1. Inspect the entire existing repository.
2. Identify:
   - frontend
   - backend
   - database
   - authentication
   - RBAC
   - document ingestion
   - existing RAG
   - vector database
   - LLM integration
   - storage
   - existing UI components
   - existing citation system
   - existing PDF viewer
   - existing drawing support
3. Understand the current architecture.
4. Identify what is already working.
5. Do NOT rewrite working functionality unnecessarily.
6. Reuse existing infrastructure where appropriate.
7. Create an architecture plan before making major changes.
8. Implement incrementally.
9. Run tests after each major subsystem.

Do not replace working Aegis functionality with a simplistic demo.

============================================================
1. CORE AEGIS PRINCIPLE
============================================================

Aegis must be:

                    EVIDENCE FIRST

Every important generated statement should be traceable to evidence.

The system must be able to answer:

"What source supports this statement?"

and:

"Show me exactly where in the original document this came from."

The final chain must be:

USER QUESTION
      ↓
QUERY UNDERSTANDING
      ↓
AGENT PLANNER
      ↓
RETRIEVAL STRATEGY
      ↓
MULTIPLE RETRIEVAL SYSTEMS
      ↓
RERANKING
      ↓
EVIDENCE VALIDATION
      ↓
LLM REASONING
      ↓
STRUCTURED CITATIONS
      ↓
ANSWER
      ↓
CLICK CITATION
      ↓
EXACT SOURCE LOCATION
      ↓
HIGHLIGHTED EVIDENCE

============================================================
2. AGENTIC HYBRID RAG
============================================================

Implement an agentic retrieval architecture.

Do NOT use a single retrieval method for every query.

The system should dynamically determine which retrieval strategies are required.

The retrieval agent may use:

1. Vector semantic search
2. BM25 / lexical search
3. Metadata filtering
4. Exact identifier search
5. Full-text search
6. Graph retrieval
7. Document hierarchy retrieval
8. Parent/child chunk retrieval
9. Table retrieval
10. Engineering drawing retrieval
11. OCR retrieval
12. Multi-hop retrieval
13. Cross-document retrieval
14. Temporal/version-aware retrieval

============================================================
3. QUERY ROUTER
============================================================

Create a Query Understanding / Routing Agent.

It should classify the question.

Examples:

"What is the vibration limit?"

→ technical document retrieval

"Where is PSV-204?"

→ engineering drawing retrieval

"What procedure applies to pump P-204?"

→ identifier + semantic + metadata retrieval

"Compare the 2024 and 2025 inspection reports."

→ multi-document + version-aware retrieval

"What caused the repeated failure?"

→ multi-hop reasoning + cross-document retrieval

"Show me the P&ID around PSV-204."

→ drawing retrieval + spatial navigation

"Which SOP applies to this equipment?"

→ identifier resolution + metadata + semantic retrieval

============================================================
4. AGENTIC RETRIEVAL LOOP
============================================================

Implement an iterative retrieval loop.

Example:

User:
"Why did pump P-204 fail repeatedly?"

Agent:

STEP 1
Identify P-204.

STEP 2
Search:
- equipment tag
- maintenance records
- inspection reports
- failure reports
- operating logs

STEP 3
Evaluate evidence.

STEP 4
If evidence is incomplete:
perform another retrieval.

STEP 5
Search related components.

STEP 6
Search relevant SOPs.

STEP 7
Search historical reports.

STEP 8
Cross-check evidence.

STEP 9
Construct answer.

STEP 10
Attach citations to each factual claim.

Do not force the agent to answer after a single retrieval.

============================================================
5. HYBRID RETRIEVAL
============================================================

Use multiple retrieval channels.

                    USER QUERY
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       VECTOR          BM25         GRAPH
          │              │              │
          └──────────────┼──────────────┘
                         │
                   EXACT MATCH
                         │
                  METADATA FILTER
                         │
                    RERANKER
                         │
                   FINAL EVIDENCE

Vector retrieval is useful for semantic meaning.

BM25/keyword retrieval is essential for:

- equipment tags
- instrument tags
- line numbers
- document numbers
- standards
- part numbers
- revision numbers
- exact terminology

Never assume embeddings alone are sufficient.

============================================================
6. EXACT IDENTIFIER SEARCH
============================================================

Engineering environments contain identifiers such as:

P-204
PSV-204
PT-204
XV-204
V-204
6-P-204-001
SOP-017
MRPL-P204-REV-C

These must receive special treatment.

Create an identifier-aware retrieval layer.

If the user asks:

"Where is PSV-204?"

search exact identifiers before relying on semantic similarity.

Normalize identifiers carefully.

Support:

PSV-204
PSV204
PSV 204

where appropriate.

Do NOT incorrectly merge unrelated identifiers.

============================================================
7. RERANKING
============================================================

After retrieving candidates:

1. merge results
2. deduplicate
3. rerank
4. evaluate relevance
5. select evidence

Use a reranker where available.

Consider:

- semantic relevance
- exact identifier match
- document authority
- revision
- date
- source type
- metadata
- user permissions
- section relevance
- proximity of terms
- engineering object relevance

============================================================
8. DOCUMENT AUTHORITY
============================================================

Not every document is equally authoritative.

Represent document metadata such as:

document_type
document_status
revision
effective_date
approval_status
department
equipment
project
plant
area
classification

Examples:

APPROVED
SUPERSEDED
DRAFT
OBSOLETE

The retrieval system must understand document status.

If two documents conflict:

do not silently choose one.

Explain the conflict and cite both sources.

============================================================
9. TEMPORAL / REVISION-AWARE RAG
============================================================

Engineering information changes over time.

Support:

document revisions
effective dates
superseded documents
historical records

Example:

P&ID Rev B
P&ID Rev C
P&ID Rev D

If the user asks:

"What is the current configuration?"

prefer the current approved revision.

If the user asks:

"What was the configuration in 2023?"

retrieve the historically appropriate revision.

Never silently mix revisions.

============================================================
10. DOCUMENT INGESTION
============================================================

Build a robust ingestion pipeline.

Support:

- PDF
- scanned PDF
- DOCX
- XLSX
- CSV
- TXT
- images
- engineering drawings

Pipeline:

UPLOAD
 ↓
FILE VALIDATION
 ↓
DOCUMENT CLASSIFICATION
 ↓
OCR / TEXT EXTRACTION
 ↓
PAGE/SHEET EXTRACTION
 ↓
LAYOUT ANALYSIS
 ↓
TABLE EXTRACTION
 ↓
ENGINEERING ENTITY EXTRACTION
 ↓
CHUNKING
 ↓
METADATA EXTRACTION
 ↓
EMBEDDING
 ↓
LEXICAL INDEX
 ↓
VECTOR INDEX
 ↓
GRAPH INDEX
 ↓
PROVENANCE STORE

============================================================
11. SMART CHUNKING
============================================================

Do not blindly chunk every document by fixed character count.

Use document-aware chunking.

Preserve:

- page
- section
- subsection
- heading
- paragraph
- table
- figure
- caption
- document revision
- equipment
- drawing sheet

Use parent-child relationships.

Example:

Document
  └── Section
       └── Subsection
            └── Chunk

A retrieved child chunk should be able to retrieve its parent context.

============================================================
12. PDF PROVENANCE
============================================================

Every chunk must preserve exact provenance.

Example:

{
  "chunk_id": "chunk_123",
  "document_id": "doc_456",
  "page": 17,
  "text": "...",
  "char_start": 18340,
  "char_end": 18520,
  "bbox": [
    {
      "x": 120,
      "y": 340,
      "width": 420,
      "height": 80
    }
  ]
}

Do not lose coordinates during ingestion.

============================================================
13. ENGINEERING DRAWINGS
============================================================

Engineering drawings are first-class Aegis objects.

Support:

- P&ID
- PFD
- GA
- piping isometric
- electrical drawing
- control schematic
- plot plan
- equipment drawing
- layout

Do NOT treat engineering drawings as ordinary text PDFs.

============================================================
14. P&ID INTELLIGENCE
============================================================

For P&IDs identify where possible:

- equipment tags
- pump tags
- vessel tags
- valve tags
- instrument tags
- line numbers
- process lines
- control loops
- connections
- arrows
- callouts
- notes

Examples:

P-204
V-204
PSV-204
PT-204
XV-204
6-P-204-001

Store spatial information.

Example:

{
  "object_type": "equipment",
  "tag": "P-204",
  "sheet": 2,
  "bbox": {
    "x": 4832,
    "y": 2170,
    "width": 180,
    "height": 120
  }
}

============================================================
15. DRAWING GRAPH
============================================================

Where reliable, represent engineering relationships as a graph.

Example:

P-204
  │
  ├── connected_to → XV-204
  │
  ├── protected_by → PSV-204
  │
  └── connected_to → Line 6-P-204-001

Graph entities:

Equipment
Instrument
Valve
Line
Vessel
Pump
Compressor
Heat exchanger
Header
Area
System

Graph relationships:

CONNECTED_TO
PROTECTED_BY
CONTROLLED_BY
FED_BY
DISCHARGES_TO
UPSTREAM_OF
DOWNSTREAM_OF
LOCATED_IN
PART_OF

Do not fabricate relationships.

Only create relationships when supported by extracted evidence or verified engineering logic.

============================================================
16. ENGINEERING DRAWING VIEWER
============================================================

Build an Aegis Evidence Viewer.

For PDFs:

Use a real PDF rendering system.

For engineering drawings:

provide a high-resolution canvas/document viewer.

Support:

- zoom
- pan
- fit drawing
- fit width
- sheet navigation
- search
- object highlighting
- region highlighting
- line highlighting
- text highlighting

============================================================
17. CITATION EXPERIENCE
============================================================

The answer may look like:

"The PSV-204 discharge is routed to the flare header. [1]"

Clicking [1]:

1. opens source
2. selects document
3. selects page/sheet
4. zooms to evidence
5. highlights evidence
6. shows surrounding context

For a normal PDF:

highlight exact text.

For a P&ID:

highlight:

PSV-204
+
relevant piping
+
flare header

when supported by the evidence.

============================================================
18. STRUCTURED CITATIONS
============================================================

Never use citations as plain strings internally.

Use structured citation objects.

Example:

{
  "citation_id": "citation_1",

  "document_id": "doc_123",

  "document_name": "P204_PandID_RevC.pdf",

  "document_type": "engineering_drawing",

  "drawing_type": "P&ID",

  "revision": "C",

  "sheet": 2,

  "page": 2,

  "target": {
    "type": "equipment",
    "tag": "PSV-204"
  },

  "excerpt": "PSV-204",

  "geometry": {
    "type": "bbox",
    "x": 4832,
    "y": 2170,
    "width": 180,
    "height": 120
  }
}

============================================================
19. CITATION INTEGRITY
============================================================

The LLM must NEVER invent citations.

The model can only cite retrieved evidence IDs.

If the system cannot find supporting evidence:

say:

"I could not find sufficient evidence in the available sources."

Do not manufacture an answer.

============================================================
20. CLAIM-LEVEL CITATIONS
============================================================

Citations should attach to claims.

Bad:

"Pump P-204 is located in Area 3, uses seal type X, and failed three times. [1]"

if [1] only supports the location.

Better:

"Pump P-204 is located in Area 3. [1]
The maintenance record specifies seal type X. [2]
The records show three failures during the reviewed period. [3]"

Citation precision is important.

============================================================
21. EVIDENCE VERIFICATION AGENT
============================================================

Before final answer generation, optionally run an evidence verification stage.

For each important claim:

CLAIM
 ↓
SUPPORTING EVIDENCE
 ↓
VERIFY
 ↓
SUPPORTED / PARTIAL / UNSUPPORTED

Unsupported claims should not be presented as established facts.

============================================================
22. CONFLICT DETECTION
============================================================

If sources disagree:

detect it.

Example:

Document A:
PSV-204 set pressure = 10 bar

Document B:
PSV-204 set pressure = 12 bar

Do not silently merge.

Return:

"Two sources report different set pressures."

Then cite both.

Include:

document
revision
date
status

where available.

============================================================
23. CONFIDENCE
============================================================

Do not create fake numerical confidence scores merely to make the UI look sophisticated.

Instead track evidence quality internally using factors such as:

- retrieval relevance
- source authority
- exact identifier match
- citation completeness
- agreement across sources
- document status
- revision consistency

Expose confidence to users only when it has a clearly defined meaning.

============================================================
24. AGENT TOOLS
============================================================

Create explicit tools for the retrieval agent.

Examples:

search_semantic()
search_keyword()
search_identifier()
search_metadata()
search_documents()
search_drawings()
search_equipment()
search_graph()
search_tables()
get_document()
get_page()
get_drawing_sheet()
get_source_context()
verify_evidence()
compare_documents()

The agent should select tools dynamically.

============================================================
25. QUERY DECOMPOSITION
============================================================

For complex questions:

"Why did pump P-204 repeatedly trip and what maintenance action should be taken?"

decompose into:

1. Identify P-204.
2. Find trip records.
3. Find historical maintenance.
4. Find inspection reports.
5. Find relevant operating conditions.
6. Find applicable SOP.
7. Compare evidence.
8. Build explanation.
9. Cite each conclusion.

Do not attempt to answer complex questions from one vector search.

============================================================
26. MULTI-HOP RETRIEVAL
============================================================

Support:

Question
 ↓
Entity
 ↓
Related entity
 ↓
Document
 ↓
Evidence
 ↓
Second document
 ↓
Verification

Example:

P-204
 ↓
Seal failure
 ↓
Maintenance record
 ↓
SOP
 ↓
Required inspection
 ↓
Conclusion

============================================================
27. TABLE INTELLIGENCE
============================================================

Tables must remain structured.

Do not convert tables into meaningless paragraphs.

Store:

table
row
column
cell
page
coordinates

Allow retrieval such as:

"What is the vibration limit for P-204?"

and cite the exact table cell if possible.

============================================================
28. DOCUMENT COMPARISON
============================================================

Support:

Compare Rev B and Rev C.

Compare two inspection reports.

Compare two SOP versions.

Show:

Added
Removed
Changed
Unchanged

Every important difference should have source provenance.

============================================================
29. CHAT UX
============================================================

Aegis chat should support:

- streaming answers
- citations
- expandable source previews
- citation click
- evidence viewer
- follow-up questions
- conversation history
- source filtering
- document filtering
- date filtering
- revision filtering
- project/plant/area filtering

============================================================
30. SOURCE PANEL
============================================================

When hovering/clicking a citation:

show:

Document
Page/Sheet
Revision
Source excerpt
Document status

Then:

[Open Evidence]

opens the full viewer.

============================================================
31. EVIDENCE VIEWER
============================================================

Build one unified component:

AegisEvidenceViewer

It determines the viewer type.

Technical document:
→ PDF viewer

Engineering drawing:
→ Drawing viewer

Spreadsheet:
→ Spreadsheet viewer

Image:
→ Image viewer

All viewers share the same:

citation
provenance
authorization
audit
navigation

architecture.

============================================================
32. RBAC
============================================================

Aegis is an enterprise/on-premise platform.

Every retrieval result must respect permissions.

Never:

retrieve everything
then filter in the UI.

Authorization must occur before evidence reaches the LLM.

The agent must only retrieve documents the user is authorized to access.

============================================================
33. SECURITY
============================================================

Protect:

- documents
- drawings
- metadata
- embeddings
- graph
- citations
- source URLs

Do not expose internal storage paths.

Do not expose unrestricted object storage URLs.

Validate authorization server-side.

Prevent IDOR vulnerabilities.

============================================================
34. AUDIT
============================================================

Audit:

- user
- query
- documents retrieved
- citations used
- evidence opened
- drawing sheet opened
- timestamp
- agent actions
- tool calls
- final answer

Provide an audit trail suitable for enterprise environments.

============================================================
35. SOVEREIGN / ON-PREMISE
============================================================

Aegis must be deployable without requiring external cloud services for core functionality.

Design for:

- self-hosted LLM
- local embedding models
- local reranker
- local vector database
- local search engine
- local object storage
- local OCR
- local document processing

Cloud integrations may be optional.

The architecture must not depend on them.

============================================================
36. MODEL ABSTRACTION
============================================================

Do not hard-code the application to one LLM.

Create an abstraction layer:

LLMProvider

EmbeddingProvider

RerankerProvider

OCRProvider

Allow different providers to be configured.

Examples may include:

- local models
- enterprise APIs
- cloud APIs

but the core Aegis architecture must remain provider-independent.

============================================================
37. OBSERVABILITY
============================================================

Track:

query latency
retrieval latency
number of candidates
reranking latency
LLM latency
tokens
tool calls
citation count
retrieval failures
unsupported claims
agent iterations

Provide useful debugging information to administrators without exposing sensitive document contents unnecessarily.

============================================================
38. AGENT TRACE
============================================================

For administrators/developers, provide an optional agent trace.

Example:

User Query
 ↓
Query Classification
 ↓
Identifier Search: PSV-204
 ↓
Vector Search
 ↓
BM25 Search
 ↓
Drawing Search
 ↓
Reranking
 ↓
Evidence Verification
 ↓
Answer Generation

Do not necessarily expose internal chain-of-thought.

Show concise tool/action summaries rather than private reasoning.

============================================================
39. PERFORMANCE
============================================================

The system must remain responsive for large enterprise repositories.

Use:

- caching
- parallel retrieval
- batched embeddings
- async ingestion
- incremental indexing
- deduplication
- efficient pagination
- streaming
- retrieval limits

Do not retrieve thousands of chunks into the LLM.

============================================================
40. DATABASE / INDEXING
============================================================

Design appropriate schemas for:

documents
document_versions
document_pages
document_chunks
document_entities
document_relationships
document_tables
document_embeddings
citations
citation_geometry
users
permissions
audit_events

Use appropriate search indexes.

============================================================
41. DOCUMENT ENTITY MODEL
============================================================

Create normalized entities where useful:

Asset
Equipment
Instrument
Valve
Line
Document
Drawing
Procedure
Inspection
MaintenanceRecord
Project
Plant
Area
System

Connect these through provenance-backed relationships.

============================================================
42. KNOWLEDGE GRAPH
============================================================

The graph should complement—not replace—the vector database.

Use vector retrieval for semantic similarity.

Use lexical retrieval for exact terminology.

Use graph retrieval for relationships.

Use metadata for filtering.

Use reranking to combine candidates.

============================================================
43. RETRIEVAL FUSION
============================================================

Implement a retrieval fusion layer.

Conceptually:

Vector Results
      +
BM25 Results
      +
Identifier Results
      +
Graph Results
      +
Metadata Results
      +
Drawing Results
      ↓
Deduplicate
      ↓
Normalize
      ↓
Rerank
      ↓
Evidence Selection

============================================================
44. ANSWER GENERATION
============================================================

The final answer generator receives:

- user question
- retrieved evidence
- source metadata
- citation IDs
- document authority
- revision information
- conflicts

The answer must:

- answer the question directly
- distinguish evidence from inference
- cite factual claims
- mention conflicts
- avoid unsupported claims
- avoid invented sources

============================================================
45. ANSWER FORMAT
============================================================

Example:

The available maintenance records indicate that P-204 experienced
three recorded trips during the reviewed period. [1][2]

The inspection report attributes two of those events to elevated
bearing temperature. [3]

The applicable procedure requires inspection of the lubrication
system under these conditions. [4]

Sources:
[1] Maintenance Log — Page 12
[2] Trip Report — Page 4
[3] Inspection Report — Page 18
[4] SOP-017 — Section 3.2

Each citation must be clickable.

============================================================
46. ENGINEERING EVIDENCE EXAMPLE
============================================================

User:

"Where is PSV-204 and where does it discharge?"

Agent:

1. exact identifier search → PSV-204
2. drawing search → P&ID P204
3. identify sheet
4. retrieve spatial region
5. inspect connected line
6. identify destination
7. verify against available documentation
8. answer

Example:

"PSV-204 is shown on P&ID P204, Sheet 2. [1]
The discharge line is shown routing toward the flare header. [1]"

Click [1]:

→ P204
→ Sheet 2
→ zoom to PSV-204
→ highlight PSV-204
→ highlight discharge line
→ show flare header context

============================================================
47. FAILURE BEHAVIOR
============================================================

If retrieval fails:

Do not hallucinate.

Say that evidence was not found.

If evidence is weak:

say so.

If documents conflict:

show the conflict.

If the requested document is inaccessible:

do not reveal its contents.

If the drawing cannot be reliably interpreted:

do not claim object-level certainty.

============================================================
48. FRONTEND ARCHITECTURE
============================================================

Create reusable components such as:

AegisChat
AegisCitation
AegisSourcePreview
AegisEvidenceViewer
AegisPdfViewer
AegisDrawingViewer
AegisSheetNavigator
AegisHighlightLayer
AegisSourcePanel
AegisDocumentSearch
AegisDrawingSearch
AegisAgentTrace

Keep the UI consistent with the existing Aegis design system.

============================================================
49. BACKEND ARCHITECTURE
============================================================

Create logical services:

QueryService
AgentService
RetrievalService
HybridSearchService
RerankingService
EvidenceService
CitationService
DocumentService
DrawingService
GraphService
IngestionService
OCRService
AuthorizationService
AuditService

Avoid creating unnecessary microservices if the existing Aegis architecture is a modular monolith.

Prefer clear boundaries over premature distributed architecture.

============================================================
50. API DESIGN
============================================================

Design APIs around capabilities rather than UI hacks.

Examples:

POST /api/rag/query

POST /api/search

POST /api/search/hybrid

GET /api/documents/:id

GET /api/documents/:id/pages/:page

GET /api/drawings/:id/sheets/:sheet

GET /api/evidence/:citationId

GET /api/citations/:citationId

POST /api/evidence/verify

The exact routes may differ depending on the existing Aegis backend.

============================================================
51. TESTING
============================================================

Create tests for:

- semantic retrieval
- BM25 retrieval
- identifier retrieval
- hybrid fusion
- reranking
- query routing
- agent iteration
- citation integrity
- authorization
- document revisions
- conflicting sources
- PDF highlighting
- drawing highlighting
- P&ID navigation
- OCR fallback
- table retrieval
- multi-hop retrieval

============================================================
52. END-TO-END ACCEPTANCE TEST
============================================================

The final system must support this complete flow:

1. Upload:

P204_PandID_RevC.pdf

2. Aegis processes it.

3. A user asks:

"Where is PSV-204 and where does it discharge?"

4. Agent determines this requires engineering drawing retrieval.

5. Exact identifier search finds PSV-204.

6. Drawing retrieval finds the correct P&ID.

7. Spatial metadata identifies PSV-204.

8. Connected line evidence is retrieved.

9. Agent verifies the evidence.

10. Answer is generated.

11. Answer contains:

[1]

12. User clicks [1].

13. Aegis opens the actual P&ID.

14. Correct sheet opens.

15. Viewer automatically zooms to PSV-204.

16. PSV-204 is highlighted.

17. Relevant discharge piping is highlighted if supported.

18. Surrounding drawing context remains visible.

19. User can zoom out and inspect the entire P&ID.

20. User can click another citation and navigate to another source.

This is the minimum acceptable experience.

============================================================
53. SECOND ACCEPTANCE TEST
============================================================

Upload:

Annual_Maintenance_Report.pdf

Ask:

"What were the major maintenance issues with P-204?"

The system must:

- retrieve relevant maintenance sections
- use semantic retrieval
- use identifier retrieval for P-204
- rerank evidence
- produce claim-level citations
- open exact pages
- highlight exact source text

============================================================
54. THIRD ACCEPTANCE TEST
============================================================

Ask:

"Compare P&ID Rev B and Rev C around P-204."

The system must:

- identify both revisions
- open corresponding sheets
- locate P-204 in each
- identify relevant differences where reliably detected
- show evidence