"""
Consent Guard — FastAPI application entry point.

A compliance governance layer that detects manipulative agent-to-customer
messaging mapped to India's Central Consumer Protection Authority (CCPA)
2023 dark-pattern guidelines before it reaches a customer, independent of
whether the message stayed within numeric spend/discount guardrails.

Built for Razorpay's AI Buildathon, Track 1 (Agentic Commerce).
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router
import models_db
from database import engine

# Load environment variables from .env file.
load_dotenv()

# Create SQLite database tables if they do not exist
models_db.Base.metadata.create_all(bind=engine)

# Configure logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

app = FastAPI(
    title="Consent Guard",
    description=(
        "Compliance governance layer for AI commerce agents. "
        "Detects dark-patterns in agent-to-customer messages using "
        "India CCPA 2023 guideline-aligned categories "
        "before they reach the customer."
    ),
    version="1.0.0",
)

# CORS — allow the Next.js frontend dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes.
app.include_router(router)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "consent-guard",
        "status": "running",
        "version": "1.0.0",
    }
