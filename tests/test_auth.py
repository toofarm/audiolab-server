def test_login_user(client):
    # Register the user first
    client.post("/auth/register", json={
        "email": "authuser@example.com",
        "password": "securepassword"
    })

    # Then login
    response = client.post("/login", data={
        "username": "authuser@example.com",
        "password": "securepassword"
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
