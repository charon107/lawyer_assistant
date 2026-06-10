"""API v1 router aggregation."""
# ruff: noqa: I001 - Imports structured for Jinja2 template conditionals

from fastapi import APIRouter

from app.api.routes.v1 import health
from app.api.routes.v1 import admin_ratings, auth, users
from app.api.routes.v1 import conversations
from app.api.routes.v1 import admin_conversations
from app.api.routes.v1 import admin_logs, admin_system
from app.api.routes.v1 import agent
from app.api.routes.v1 import files
from app.api.routes.v1 import commercial
from app.api.routes.v1 import commercial_ws
from app.api.routes.v1 import corporate
from app.api.routes.v1 import corporate_ws
from app.api.routes.v1 import employment
from app.api.routes.v1 import employment_ws
from app.api.routes.v1 import privacy
from app.api.routes.v1 import privacy_ws
from app.api.routes.v1 import ip
from app.api.routes.v1 import ip_ws

v1_router = APIRouter()

# Health check routes (no auth required)
v1_router.include_router(health.router, tags=["health"])

# Authentication routes
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User routes
v1_router.include_router(users.router, prefix="/users", tags=["users"])

# Admin routes
v1_router.include_router(admin_ratings.router, prefix="/admin/ratings", tags=["admin:ratings"])

# Conversation routes (AI chat persistence)
v1_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])


# AI Agent routes
v1_router.include_router(agent.router, tags=["agent"])

# File upload/download routes
v1_router.include_router(files.router, tags=["files"])

# Admin: conversation browser + user listing
v1_router.include_router(
    admin_conversations.router, prefix="/admin/conversations", tags=["admin-conversations"]
)

# Commercial-legal module (Phase A)
v1_router.include_router(commercial.router, prefix="/commercial", tags=["commercial"])
v1_router.include_router(commercial_ws.router, tags=["commercial-ws"])

# Corporate-legal module (公司并购) — Phase 1 (M&A core)
v1_router.include_router(corporate.router, prefix="/corporate", tags=["corporate"])
v1_router.include_router(corporate_ws.router, tags=["corporate-ws"])

# Employment-legal module (劳动用工)
v1_router.include_router(employment.router, prefix="/employment", tags=["employment"])
v1_router.include_router(employment_ws.router, tags=["employment-ws"])

# Privacy-legal module (个人信息保护)
v1_router.include_router(privacy.router, prefix="/privacy", tags=["privacy"])
v1_router.include_router(privacy_ws.router, tags=["privacy-ws"])

# IP-legal module (知识产权)
v1_router.include_router(ip.router, prefix="/ip", tags=["ip"])
v1_router.include_router(ip_ws.router, tags=["ip-ws"])

# Admin: system status (RAG health) and logs
v1_router.include_router(admin_system.router, prefix="/admin/system", tags=["admin:system"])
v1_router.include_router(admin_logs.router, prefix="/admin/logs", tags=["admin:logs"])
