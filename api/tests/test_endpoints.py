import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    os.environ["STORAGE_PATH"] = str(tmp_path / "test.db")
    yield
    os.environ.pop("STORAGE_PATH", None)


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


TIMINGS = [100.0, 80.0, 60.0, 90.0, 75.0, 85.0, 95.0, 70.0, 88.0, 92.0]


class TestRoot:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["message"] == "KeyCadence API"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestEnroll:
    def test_enroll_success(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        })
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "alice"
        assert data["status"] == "enrolled"
        assert data["samples_recorded"] == len(TIMINGS)

    def test_enroll_empty_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": []
        })
        assert r.status_code == 500

    def test_enroll_reenroll_overwrites(self, client):
        r1 = client.post("/enroll", json={
            "user_id": "carol",
            "keystroke_timings": TIMINGS
        })
        assert r1.status_code == 200
        r2 = client.post("/enroll", json={
            "user_id": "carol",
            "keystroke_timings": [200.0, 200.0, 200.0]
        })
        assert r2.status_code == 200
        assert r2.json()["samples_recorded"] == 3

    def test_enroll_missing_fields(self, client):
        r = client.post("/enroll", json={"user_id": "x"})
        assert r.status_code == 422


class TestVerify:
    def _enroll(self, client, user_id="dave", timings=TIMINGS):
        client.post("/enroll", json={
            "user_id": user_id,
            "keystroke_timings": timings
        })

    def test_verify_match(self, client):
        self._enroll(client)
        r = client.post("/verify", json={
            "user_id": "dave",
            "keystroke_timings": TIMINGS
        })
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "ALLOW"
        assert data["flagged"] is False
        assert data["match_confidence"] > 0.5

    def test_verify_mismatch(self, client):
        self._enroll(client, user_id="eve")
        r = client.post("/verify", json={
            "user_id": "eve",
            "keystroke_timings": [500.0, 600.0, 700.0, 800.0, 900.0,
                                  500.0, 600.0, 700.0, 800.0, 900.0]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "BLOCK"
        assert data["flagged"] is True
        assert data["match_confidence"] < 0.3

    def test_verify_not_enrolled(self, client):
        r = client.post("/verify", json={
            "user_id": "nobody",
            "keystroke_timings": TIMINGS
        })
        assert r.status_code == 404
        assert "not enrolled" in r.json()["detail"]

    def test_verify_partial_match(self, client):
        self._enroll(client, user_id="frank")
        slightly_off = [t + 2.0 for t in TIMINGS]
        r = client.post("/verify", json={
            "user_id": "frank",
            "keystroke_timings": slightly_off
        })
        assert r.status_code == 200
        data = r.json()
        assert data["match_confidence"] > 0.7
        assert data["decision"] == "ALLOW"

    def test_verify_response_fields(self, client):
        self._enroll(client, user_id="gina")
        r = client.post("/verify", json={
            "user_id": "gina",
            "keystroke_timings": TIMINGS
        })
        data = r.json()
        assert set(data.keys()) == {
            "user_id", "match_confidence", "decision", "reason", "flagged"
        }
