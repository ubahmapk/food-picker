def test_index_serves_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Food Picker" in response.data
    assert b"text/html" in response.content_type.encode()
