from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, analyze, auth, explore, history, mentor, onboarding, quiz


app = FastAPI(
    title="DUO MIND API",
    description="AI-powered knowledge analysis and education platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins or ["http://localhost:3001"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(explore.router, prefix="/api/explore", tags=["explore"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "DUO MIND API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "app": "DUO MIND API"}
