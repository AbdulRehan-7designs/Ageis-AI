# Aegis AI — Demo Walkthrough

> This is a recording checklist, not a link to an existing live demo. Record the application only after verifying the full flow locally.

## Before recording

- [ ] Start the Docker Compose stack and wait for health checks.
- [ ] Confirm the frontend, API, PostgreSQL, Qdrant, Redis, Ollama, and sandbox services are healthy.
- [ ] Configure local models required by the selected demo flow.
- [ ] Use public or synthetic engineering documents only.
- [ ] Create demo users with different roles/clearance levels.
- [ ] Remove secrets, tokens, private URLs, and personal information from the recording.

## Suggested 3–4 minute walkthrough

1. **Problem (20 seconds):** Explain that engineering evidence is spread across manuals, reports, drawings, and inspection documents.
2. **Document ingestion (40 seconds):** Upload one safe sample PDF and show its document metadata.
3. **Grounded question (50 seconds):** Ask a question whose answer is explicitly present in the sample document.
4. **Evidence inspection (40 seconds):** Open the citations and verify the document name, page, and highlighted evidence.
5. **Access boundary (30 seconds):** Show that a user with insufficient clearance cannot retrieve restricted evidence. Use test accounts and non-sensitive sample files.
6. **Agent/audit trace (30 seconds):** Show the saved run or audit event, if available in the current build.
7. **Artifact workflow (30 seconds):** Generate a draft report and explain the review status. Do not imply AI output is engineering approval.

## Recording notes

- Show the application version/commit used for the recording.
- Do not claim a feature works unless you demonstrate it during the recording.
- If a step fails, document it rather than editing the recording to imply success.
- Add the finished video URL to the main README only after the video is uploaded and publicly accessible.
