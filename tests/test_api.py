from fastapi.testclient import TestClient
from server import app

def test_state(client=None):
    c = TestClient(app)
    r = c.get("/api/state")
    assert r.status_code == 200
    d = r.json()
    assert {"customers", "recent", "hisaab", "stt_available"} <= set(d)

def test_entry_and_undo():
    c = TestClient(app)
    r = c.post("/api/entry", json={"text": "Testuser ko 111 udhaar diya"})
    assert r.status_code == 200
    d = r.json()
    assert d["action"]["amount"] == 111
    r2 = c.post(f"/api/undo/{d['action']['id']}")
    assert r2.json()["ok"]

def test_hisaab_endpoint_shape():
    c = TestClient(app)
    d = c.get("/api/state").json()["hisaab"]
    for k in ["bikri", "jama", "udhaar_diya", "kharcha", "net_cash", "total_outstanding", "date"]:
        assert k in d
