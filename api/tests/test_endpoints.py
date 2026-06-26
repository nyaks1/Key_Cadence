import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    os.environ["STORAGE_PATH"] = str(tmp_path / "test.db")
    os.environ["VALID_API_KEYS"] = "test-key-1,test-key-2"
    yield
    os.environ.pop("STORAGE_PATH", None)
    os.environ.pop("VALID_API_KEYS", None)


@pytest.fixture
def client():
    from api.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


HEADERS = {"X-API-Key": "test-key-1"}
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


class TestAuth:
    def test_missing_api_key(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        })
        assert r.status_code == 403
        assert "Missing" in r.json()["detail"]

    def test_invalid_api_key(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        }, headers={"X-API-Key": "wrong-key"})
        assert r.status_code == 403
        assert "Invalid" in r.json()["detail"]

    def test_second_valid_key_works(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        }, headers={"X-API-Key": "test-key-2"})
        assert r.status_code == 200

    def test_empty_string_key(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        }, headers={"X-API-Key": ""})
        assert r.status_code == 403

    def test_auth_required_on_verify(self, client):
        r = client.post("/verify", json={
            "user_id": "nobody",
            "keystroke_timings": TIMINGS
        })
        assert r.status_code == 403

    def test_auth_required_on_delete(self, client):
        r = client.delete("/user/ghost")
        assert r.status_code == 403


class TestEnroll:
    def test_enroll_success(self, client):
        r = client.post("/enroll", json={
            "user_id": "alice",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "alice"
        assert data["status"] == "enrolled"
        assert data["samples_recorded"] == len(TIMINGS)

    def test_enroll_empty_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": []
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_too_few_samples(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": [100.0, 80.0]
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_exactly_four_samples(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": [100.0, 80.0, 60.0, 90.0]
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_exactly_five_samples(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": [100.0, 80.0, 60.0, 90.0, 75.0]
        }, headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["samples_recorded"] == 5

    def test_enroll_single_sample(self, client):
        r = client.post("/enroll", json={
            "user_id": "bob",
            "keystroke_timings": [100.0]
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_reenroll_overwrites(self, client):
        r1 = client.post("/enroll", json={
            "user_id": "carol",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r1.status_code == 200
        new_timings = [200.0, 200.0, 200.0, 200.0, 200.0]
        r2 = client.post("/enroll", json={
            "user_id": "carol",
            "keystroke_timings": new_timings
        }, headers=HEADERS)
        assert r2.status_code == 200
        assert r2.json()["samples_recorded"] == 5

    def test_enroll_missing_fields(self, client):
        r = client.post("/enroll", json={"user_id": "x"}, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_path_traversal(self, client):
        r = client.post("/enroll", json={
            "user_id": "../etc/passwd",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_sql_injection(self, client):
        r = client.post("/enroll", json={
            "user_id": "'; DROP TABLE baselines;--",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_too_short(self, client):
        r = client.post("/enroll", json={
            "user_id": "ab",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_exactly_three_chars(self, client):
        r = client.post("/enroll", json={
            "user_id": "abc",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_user_id_exactly_64_chars(self, client):
        r = client.post("/enroll", json={
            "user_id": "a" * 64,
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_user_id_65_chars(self, client):
        r = client.post("/enroll", json={
            "user_id": "a" * 65,
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_with_hyphens(self, client):
        r = client.post("/enroll", json={
            "user_id": "user-name_123",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_user_id_with_spaces(self, client):
        r = client.post("/enroll", json={
            "user_id": "user name",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_with_special_chars(self, client):
        r = client.post("/enroll", json={
            "user_id": "user@name!",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_empty_string(self, client):
        r = client.post("/enroll", json={
            "user_id": "",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_user_id_unicode(self, client):
        r = client.post("/enroll", json={
            "user_id": "usér",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_enroll_all_same_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "same",
            "keystroke_timings": [100.0, 100.0, 100.0, 100.0, 100.0]
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_very_large_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "large",
            "keystroke_timings": [999999.0, 888888.0, 777777.0, 666666.0, 555555.0]
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_zero_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "zeros",
            "keystroke_timings": [0.0, 0.0, 0.0, 0.0, 0.0]
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_negative_timings(self, client):
        r = client.post("/enroll", json={
            "user_id": "neg",
            "keystroke_timings": [-10.0, -20.0, -30.0, -40.0, -50.0]
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_enroll_many_samples(self, client):
        timings = [float(i) for i in range(1000)]
        r = client.post("/enroll", json={
            "user_id": "many",
            "keystroke_timings": timings
        }, headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["samples_recorded"] == 1000

    def test_enroll_body_not_json(self, client):
        r = client.post("/enroll", content="not json", headers={
            **HEADERS, "Content-Type": "text/plain"
        })
        assert r.status_code == 422

    def test_enroll_empty_body(self, client):
        r = client.post("/enroll", json={}, headers=HEADERS)
        assert r.status_code == 422


class TestVerify:
    def _enroll(self, client, user_id="dave", timings=TIMINGS):
        client.post("/enroll", json={
            "user_id": user_id,
            "keystroke_timings": timings
        }, headers=HEADERS)

    def test_verify_match(self, client):
        self._enroll(client)
        r = client.post("/verify", json={
            "user_id": "dave",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
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
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "BLOCK"
        assert data["flagged"] is True
        assert data["match_confidence"] < 0.3

    def test_verify_not_enrolled(self, client):
        r = client.post("/verify", json={
            "user_id": "nobody",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 404
        assert "not enrolled" in r.json()["detail"]

    def test_verify_partial_match(self, client):
        self._enroll(client, user_id="frank")
        slightly_off = [t + 2.0 for t in TIMINGS]
        r = client.post("/verify", json={
            "user_id": "frank",
            "keystroke_timings": slightly_off
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["match_confidence"] > 0.7
        assert data["decision"] == "ALLOW"

    def test_verify_response_fields(self, client):
        self._enroll(client, user_id="gina")
        r = client.post("/verify", json={
            "user_id": "gina",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        data = r.json()
        assert set(data.keys()) == {
            "user_id", "match_confidence", "decision", "reason", "flagged"
        }

    def test_verify_exact_same_timings(self, client):
        self._enroll(client, user_id="exact")
        r = client.post("/verify", json={
            "user_id": "exact",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["match_confidence"] > 0.5
        assert data["decision"] == "ALLOW"

    def test_verify_all_same_timings(self, client):
        self._enroll(client, user_id="same", timings=[100.0] * 10)
        r = client.post("/verify", json={
            "user_id": "same",
            "keystroke_timings": [100.0] * 10
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["match_confidence"] == 1.0
        assert data["decision"] == "ALLOW"

    def test_verify_after_delete(self, client):
        self._enroll(client, user_id="deleteme")
        client.delete("/user/deleteme", headers=HEADERS)
        r = client.post("/verify", json={
            "user_id": "deleteme",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 404

    def test_verify_multiple_users_independent(self, client):
        self._enroll(client, user_id="user_a", timings=[100.0, 110.0, 120.0, 130.0, 140.0])
        self._enroll(client, user_id="user_b", timings=[500.0, 510.0, 520.0, 530.0, 540.0])

        r_a = client.post("/verify", json={
            "user_id": "user_a",
            "keystroke_timings": [100.0, 110.0, 120.0, 130.0, 140.0]
        }, headers=HEADERS)
        r_b = client.post("/verify", json={
            "user_id": "user_b",
            "keystroke_timings": [500.0, 510.0, 520.0, 530.0, 540.0]
        }, headers=HEADERS)
        assert r_a.status_code == 200
        assert r_b.status_code == 200
        assert r_a.json()["decision"] == "ALLOW"
        assert r_b.json()["decision"] == "ALLOW"

    def test_verify_user_a_timings_on_user_b_baseline(self, client):
        self._enroll(client, user_id="user_x", timings=[100.0, 110.0, 120.0, 130.0, 140.0])
        self._enroll(client, user_id="user_y", timings=[500.0, 510.0, 520.0, 530.0, 540.0])

        r = client.post("/verify", json={
            "user_id": "user_y",
            "keystroke_timings": [100.0, 110.0, 120.0, 130.0, 140.0]
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "BLOCK"
        assert data["flagged"] is True

    def test_verify_reenroll_uses_new_baseline(self, client):
        self._enroll(client, user_id="switch", timings=[100.0, 100.0, 100.0, 100.0, 100.0])
        self._enroll(client, user_id="switch", timings=[500.0, 500.0, 500.0, 500.0, 500.0])

        r = client.post("/verify", json={
            "user_id": "switch",
            "keystroke_timings": [500.0, 500.0, 500.0, 500.0, 500.0]
        }, headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["decision"] == "ALLOW"

    def test_verify_empty_timings(self, client):
        self._enroll(client, user_id="emptytest")
        r = client.post("/verify", json={
            "user_id": "emptytest",
            "keystroke_timings": []
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_verify_too_few_samples(self, client):
        self._enroll(client, user_id="fewtest")
        r = client.post("/verify", json={
            "user_id": "fewtest",
            "keystroke_timings": [100.0, 200.0]
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_verify_confidence_between_0_and_1(self, client):
        self._enroll(client, user_id="conftest")
        r = client.post("/verify", json={
            "user_id": "conftest",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200
        confidence = r.json()["match_confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_verify_decision_is_valid_enum(self, client):
        self._enroll(client, user_id="enumtest")
        r = client.post("/verify", json={
            "user_id": "enumtest",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["decision"] in ("ALLOW", "STEP_UP", "BLOCK")

    def test_verify_flagged_matches_decision(self, client):
        self._enroll(client, user_id="flagtest")
        r = client.post("/verify", json={
            "user_id": "flagtest",
            "keystroke_timings": [500.0, 600.0, 700.0, 800.0, 900.0,
                                  500.0, 600.0, 700.0, 800.0, 900.0]
        }, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["flagged"] == (data["decision"] != "ALLOW")

    def test_verify_missing_fields(self, client):
        self._enroll(client, user_id="misstest")
        r = client.post("/verify", json={"user_id": "misstest"}, headers=HEADERS)
        assert r.status_code == 422

    def test_verify_user_id_path_traversal(self, client):
        r = client.post("/verify", json={
            "user_id": "../etc/passwd",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422

    def test_verify_user_id_sql_injection(self, client):
        r = client.post("/verify", json={
            "user_id": "'; DROP TABLE baselines;--",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 422


class TestDelete:
    def test_delete_success(self, client):
        client.post("/enroll", json={
            "user_id": "to_delete",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        r = client.delete("/user/to_delete", headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_delete_not_found(self, client):
        r = client.delete("/user/ghost", headers=HEADERS)
        assert r.status_code == 404

    def test_delete_requires_auth(self, client):
        client.post("/enroll", json={
            "user_id": "protected",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        r = client.delete("/user/protected")
        assert r.status_code == 403

    def test_delete_twice_returns_404_second_time(self, client):
        client.post("/enroll", json={
            "user_id": "onetime",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        r1 = client.delete("/user/onetime", headers=HEADERS)
        assert r1.status_code == 200
        r2 = client.delete("/user/onetime", headers=HEADERS)
        assert r2.status_code == 404

    def test_delete_then_enroll_again(self, client):
        client.post("/enroll", json={
            "user_id": "recycle",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        client.delete("/user/recycle", headers=HEADERS)
        r = client.post("/enroll", json={
            "user_id": "recycle",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200

    def test_delete_user_id_path_traversal(self, client):
        r = client.delete("/user/../etc/passwd", headers=HEADERS)
        assert r.status_code in (404, 422)

    def test_delete_response_structure(self, client):
        client.post("/enroll", json={
            "user_id": "struct",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        r = client.delete("/user/struct", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"status", "user_id"}
        assert data["status"] == "deleted"
        assert data["user_id"] == "struct"

    def test_delete_does_not_affect_other_users(self, client):
        client.post("/enroll", json={
            "user_id": "keep",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        client.post("/enroll", json={
            "user_id": "remove",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        client.delete("/user/remove", headers=HEADERS)

        r = client.post("/verify", json={
            "user_id": "keep",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r.status_code == 200
        assert r.json()["decision"] == "ALLOW"


class TestCrossEndpoint:
    def test_enroll_verify_delete_cycle(self, client):
        r1 = client.post("/enroll", json={
            "user_id": "cycle",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r1.status_code == 200

        r2 = client.post("/verify", json={
            "user_id": "cycle",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r2.status_code == 200
        assert r2.json()["decision"] == "ALLOW"

        r3 = client.delete("/user/cycle", headers=HEADERS)
        assert r3.status_code == 200

        r4 = client.post("/verify", json={
            "user_id": "cycle",
            "keystroke_timings": TIMINGS
        }, headers=HEADERS)
        assert r4.status_code == 404

    def test_health不受auth影响(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_root不受auth影响(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_many_users_enroll_and_verify(self, client):
        for i in range(20):
            user = f"user_{i}"
            timings = [100.0 + i] * 10
            r = client.post("/enroll", json={
                "user_id": user,
                "keystroke_timings": timings
            }, headers=HEADERS)
            assert r.status_code == 200

            r = client.post("/verify", json={
                "user_id": user,
                "keystroke_timings": timings
            }, headers=HEADERS)
            assert r.status_code == 200
            assert r.json()["decision"] == "ALLOW"
