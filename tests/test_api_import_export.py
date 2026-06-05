import json
from io import BytesIO


def test_export_toml(client):
    response = client.get("/api/export?format=toml")

    assert response.status_code == 200
    assert b"categories" in response.data
    assert b"McDonalds" in response.data


def test_export_json(client):
    response = client.get("/api/export?format=json")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "categories" in data
    assert "places" in data
    assert len(data["places"]) == 4


def test_export_invalid_format(client):
    response = client.get("/api/export?format=invalid")

    assert response.status_code == 422


def test_import_json(client):
    content = (
        b'{"categories": ["New Cat"], "places": [{"name": "New Place", "categories": ["New Cat"]}]}'
    )

    response = client.post(
        "/api/import",
        data={"file": (BytesIO(content), "test.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    places_response = client.get("/api/places")
    places = places_response.get_json()
    assert len(places) == 1
    assert places[0]["name"] == "New Place"


def test_import_toml(client):
    toml_content = (
        b'categories = ["New Cat"]\n\n[[places]]\nname = "New Place"\ncategories = ["New Cat"]'
    )

    response = client.post(
        "/api/import",
        data={"file": (BytesIO(toml_content), "test.toml")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    places_response = client.get("/api/places")
    places = places_response.get_json()
    assert len(places) == 1
    assert places[0]["name"] == "New Place"


def test_import_invalid_json(client):
    response = client.post(
        "/api/import",
        data={"file": (BytesIO(b'{"invalid": json}'), "test.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422


def test_import_no_file(client):
    response = client.post("/api/import")

    assert response.status_code == 400


def test_import_invalid_extension(client):
    response = client.post(
        "/api/import",
        data={"file": (BytesIO(b"some data"), "test.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_export_import_round_trip(client):
    export_response = client.get("/api/export?format=toml")
    original_data = export_response.data

    import_response = client.post(
        "/api/import",
        data={"file": (BytesIO(original_data), "export.toml")},
        content_type="multipart/form-data",
    )

    assert import_response.status_code == 200

    export_again = client.get("/api/export?format=toml")
    assert export_again.data == original_data
