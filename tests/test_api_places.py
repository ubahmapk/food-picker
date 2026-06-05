import pytest


def test_get_places(client):
    response = client.get("/api/places")

    assert response.status_code == 200
    places = response.get_json()
    assert len(places) == 4
    assert places[0]["name"] == "McDonalds"


def test_add_place(client):
    response = client.post(
        "/api/places",
        json={"name": "New Place", "categories": ["Fast Food"]},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "New Place"

    places_response = client.get("/api/places")
    places = places_response.get_json()
    assert len(places) == 5


def test_add_place_duplicate(client):
    response = client.post(
        "/api/places",
        json={"name": "McDonalds", "categories": ["Fast Food"]},
    )

    assert response.status_code == 422
    data = response.get_json()
    assert "already exists" in data["error"]


def test_add_place_invalid_category(client):
    response = client.post(
        "/api/places",
        json={"name": "New Place", "categories": ["NonExistent"]},
    )

    assert response.status_code == 422


def test_add_place_empty_name(client):
    response = client.post(
        "/api/places",
        json={"name": "", "categories": ["Fast Food"]},
    )

    assert response.status_code == 422


def test_add_place_no_categories(client):
    response = client.post(
        "/api/places",
        json={"name": "New Place", "categories": []},
    )

    assert response.status_code == 422


def test_delete_place(client):
    response = client.delete("/api/places/McDonalds")

    assert response.status_code == 200

    places_response = client.get("/api/places")
    places = places_response.get_json()
    assert len(places) == 3
    assert not any(p["name"] == "McDonalds" for p in places)


def test_delete_nonexistent_place(client):
    response = client.delete("/api/places/Nonexistent")

    assert response.status_code == 404


def test_update_place_name(client):
    response = client.put(
        "/api/places/McDonalds",
        json={"name": "McDonald's"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "McDonald's"


def test_update_place_categories(client):
    response = client.put(
        "/api/places/Five Guys",
        json={"categories": ["Quality Nommings"]},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["categories"] == ["Quality Nommings"]


def test_update_place_both(client):
    response = client.put(
        "/api/places/McDonalds",
        json={"name": "McDonald's", "categories": ["Quality Nommings"]},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "McDonald's"
    assert data["categories"] == ["Quality Nommings"]
