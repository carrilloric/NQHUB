"""
AI Assistant Module for NQHUB

This module provides an AI-powered assistant that can:
- Answer questions about the database using NL→SQL (Vanna.AI)
- Monitor and announce system status proactively
- Maintain conversational context using mem0
- Route queries intelligently using LangGraph

Architecture:
- llm/: Claude and Gemini client wrappers
- tools/: Vanna SQL, status monitors, system health
- services/: Orchestration, conversations, notifications
- routes.py: FastAPI endpoints
"""
