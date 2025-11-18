# Architecture

Next.js UI → FastAPI → Redis/RQ worker → per-page pipeline → ZIP download.
SQLite stores job/page progress for the live UI.

Providers are swappable in `apps/api/app/pipeline/` without changing the orchestrator flow.
