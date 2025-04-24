def test_register_user(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "strongpassword"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"
