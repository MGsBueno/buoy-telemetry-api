from fastapi.testclient import TestClient

import pytest

from app.core.config import settings
from app.main import app
from app.model import buoy_model


class FakePushResult:
    def __init__(self, key: str) -> None:
        self.key = key


class FakeDatabaseReference:
    def __init__(self, store: dict, path: str, counters: dict[str, int]) -> None:
        self.store = store
        self.path = [part for part in path.split("/") if part]
        self.counters = counters

    def _resolve_parent(self, create: bool = False):
        node = self.store
        for part in self.path[:-1]:
            current = node.get(part)
            if current is None:
                if not create:
                    return None, None
                current = {}
                node[part] = current
            node = current
        if not self.path:
            return None, None
        return node, self.path[-1]

    def _resolve_value(self):
        node = self.store
        for part in self.path:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def get(self):
        value = self._resolve_value()
        if isinstance(value, dict):
            return dict(value)
        return value

    def set(self, payload):
        parent, key = self._resolve_parent(create=True)
        parent[key] = payload

    def update(self, payload: dict):
        current = self._resolve_value()
        if current is None:
            self.set(dict(payload))
            return
        current.update(payload)

    def delete(self):
        parent, key = self._resolve_parent(create=False)
        if parent is not None and key in parent:
            del parent[key]

    def push(self, payload: dict):
        current = self._resolve_value()
        if current is None:
            self.set({})
            current = self._resolve_value()

        counter = self.counters.get("/".join(self.path), 0) + 1
        self.counters["/".join(self.path)] = counter
        key = f"reading-{counter}"
        current[key] = payload
        return FakePushResult(key)


def create_client() -> TestClient:
    return TestClient(app)


def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": settings.admin_api_token}


def build_fake_reference_factory(store: dict):
    counters: dict[str, int] = {}

    def _factory(path: str):
        return FakeDatabaseReference(store, path, counters)

    return _factory
@pytest.fixture
def functional_client(monkeypatch):
    fake_store: dict = {}

    monkeypatch.setattr(settings, "admin_api_token", "test-admin-token")
    monkeypatch.setattr(
        buoy_model,
        "get_database_reference",
        build_fake_reference_factory(fake_store),
    )
    monkeypatch.setattr(buoy_model.time, "time", lambda: 1710000000)

    return TestClient(app)
