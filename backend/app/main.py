"""Install the air-gap HTTP guard before any service creates an httpx client."""

from app.services.egress_guard import install_httpx_hooks

install_httpx_hooks()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Sovereign On-Premise Agentic AI Workbench API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/files", StaticFiles(directory="uploaded_docs"), name="files")


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
