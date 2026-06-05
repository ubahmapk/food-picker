import pytest


def test_pick_all_categories(client):
    response = client.get("/api/pick")

    assert response.status_code == 200
    data = response.get_json()
    assert "name" in data
    assert data["name"] in [
        "McDonalds",
        "Whataburger",
        "Five Guys",
        "Rosa's Cafe",
    ]


def test_pick_single_category(client):
    response = client.get("/api/pick?categories=Quality+Nommings")

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] in ["Five Guys", "Rosa's Cafe"]


def test_pick_multiple_categories(client):
    response = client.get("/api/pick?categories=Fast+Food&categories=Quality+Nommings")

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] in [
        "McDonalds",
        "Whataburger",
        "Five Guys",
        "Rosa's Cafe",
    ]


def test_pick_with_veto(client):
    response = client.get("/api/pick?vetoed=McDonalds&vetoed=Whataburger")

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] in ["Five Guys", "Rosa's Cafe"]


def test_pick_all_vetoed(client):
    response = client.get(
        "/api/pick?categories=Fast+Food&vetoed=McDonalds&vetoed=Whataburger&vetoed=Five+Guys"
    )

    assert response.status_code == 409
    data = response.get_json()
    assert data["error"] == "no options remaining"


def test_pick_invalid_category(client):
    response = client.get("/api/pick?categories=Invalid")

    assert response.status_code == 409
    data = response.get_json()
    assert data["error"] == "no options remaining"
