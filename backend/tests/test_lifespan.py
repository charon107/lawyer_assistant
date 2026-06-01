"""Application lifespan (startup/shutdown) regression tests.

These guard the FastAPI lifespan, which the async `client` fixture does not
exercise. A C1 regression shipped where `import app.db.models` inside the
lifespan shadowed the `app: FastAPI` parameter, making
`app.state.scheduler = scheduler` raise
`AttributeError: module 'app' has no attribute 'state'` on every fresh boot.
"""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_lifespan_startup_runs_without_error() -> None:
    """Entering the app context must run startup without raising.

    `TestClient` as a context manager triggers the real lifespan, unlike the
    ASGITransport-based async fixture used elsewhere.
    """
    with TestClient(app) as client:
        response = client.get(f"{settings.API_V1_STR}/health")
        assert response.status_code == 200


def test_lifespan_attaches_scheduler_to_app_state() -> None:
    """The scheduler must be reachable via `app.state`, not shadowed away."""
    with TestClient(app):
        assert hasattr(app.state, "scheduler")
        assert app.state.scheduler is not None
