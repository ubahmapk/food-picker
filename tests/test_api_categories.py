import pytest


def test_get_categories(client):
    response = client.get("/api/categories")

    assert response.status_code == 200
    categories = response.get_json()
    assert categories == ["Fast Food", "Quality Nommings"]


def test_add_category(client):
    response = client.post(
        "/api/categories",
        json={"name": "Fancy Fixings"},
    )

    assert response.status_code == 201
    categories = response.get_json()
    assert "Fancy Fixings" in categories
    assert len(categories) == 3


def test_add_category_duplicate(client):
    response = client.post(
        "/api/categories",
        json={"name": "Fast Food"},
    )

    assert response.status_code == 422
    data = response.get_json()
    assert "already exists" in data["error"]


def test_add_category_empty(client):
    response = client.post(
        "/api/categories",
        json={"name": ""},
    )

    assert response.status_code == 422


def test_delete_category(client):
    response = client.delete("/api/categories/Fast Food")

    assert response.status_code == 200

    categories_response = client.get("/api/categories")
    categories = categories_response.get_json()
    assert "Fast Food" not in categories
    assert len(categories) == 1

    places_response = client.get("/api/places")
    places = places_response.get_json()
    assert len(places) == 2
    for place in places:
        assert "Fast Food" not in place["categories"]


def test_delete_nonexistent_category(client):
    response = client.delete("/api/categories/Nonexistent")

    assert response.status_code == 404


def test_rename_category_success(client):
    response = client.put("/api/categories/Fast Food", json={"name": "Quick Bites"})

    assert response.status_code == 200
    assert response.get_json() == {"name": "Quick Bites"}

    categories = client.get("/api/categories").get_json()
    assert "Quick Bites" in categories
    assert "Fast Food" not in categories


def test_rename_category_cascades_to_places(client):
    client.put("/api/categories/Fast Food", json={"name": "Quick Bites"})

    places = client.get("/api/places").get_json()
    for place in places:
        assert "Fast Food" not in place["categories"]
    all_cats = [c for p in places for c in p["categories"]]
    assert "Quick Bites" in all_cats


def test_rename_category_same_name(client):
    response = client.put("/api/categories/Fast Food", json={"name": "Fast Food"})

    assert response.status_code == 200
    assert response.get_json() == {"name": "Fast Food"}


def test_rename_category_duplicate_rejected(client):
    response = client.put("/api/categories/Fast Food", json={"name": "Quality Nommings"})

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


def test_rename_category_not_found(client):
    response = client.put("/api/categories/Nonexistent", json={"name": "New Name"})

    assert response.status_code == 404


def test_rename_category_empty_name(client):
    response = client.put("/api/categories/Fast Food", json={"name": ""})

    assert response.status_code == 422


def test_reorder_categories(client):
    response = client.put(
        "/api/categories",
        json={"categories": ["Quality Nommings", "Fast Food"]},
    )

    assert response.status_code == 200
    categories = response.get_json()
    assert categories == ["Quality Nommings", "Fast Food"]


def test_reorder_categories_invalid(client):
    response = client.put(
        "/api/categories",
        json={"categories": ["Quality Nommings", "Invalid"]},
    )

    assert response.status_code == 422
