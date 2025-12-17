def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Мой Блог" in response.text


def test_api_users(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_posts(client):
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
