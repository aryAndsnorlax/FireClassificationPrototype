from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_hotspots_endpoint_returns_geojson_shape():
    resp = client.get("/hotspots/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert "features" in body


def test_alerts_endpoint_returns_list():
    resp = client.get("/alerts/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
