"""
Test configuration and shared fixtures.

Provides an autouse fixture that restores the app.core.config module after
tests that call importlib.reload on it with a patched environment.  Without
this, test_task_1_1_scaffold.py permanently mutates the module-level
`settings` singleton and breaks any subsequent test that imports
`from app.core.config import settings`.
"""
import importlib
import pytest


@pytest.fixture(autouse=True)
def restore_settings_module():
    """Reload app.core.config after each test to undo any importlib.reload
    side effects introduced by test_task_1_1_scaffold.py."""
    yield
    # After the test: reload the config module so the settings singleton
    # always reflects the actual (un-patched) environment.
    import app.core.config as cfg
    importlib.reload(cfg)
    # Also reload auth_service so it picks up the fresh settings reference.
    try:
        import app.services.auth_service as svc
        importlib.reload(svc)
    except Exception:
        pass
