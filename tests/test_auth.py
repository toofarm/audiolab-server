def test_login_user(client):
    # Register the user first
    registration_response = client.post("/auth/register", json={
        "first_name": "Auth",
        "last_name": "User",
        "email": "authuser@example.com",
        "password": "securepassword"
    })

    assert registration_response.status_code == 200

    # Then login
    response = client.post("/auth/login", data={
        "username": "authuser@example.com",
        "password": "securepassword",
    })

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
