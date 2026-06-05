def test_about_returns_200(client):
    response = client.get("/api/about")

    assert response.status_code == 200
    data = response.get_json()
    assert "name" in data
    assert data["name"] == "Food Picker"
    assert "tech" in data
    assert isinstance(data["tech"], list)
