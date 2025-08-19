
auth_prefix = f"/api/v1/auth"

def test_user_creation(fake_session, fake_user_service, test_client):
    signup_data = {
            "first_name": "hibah",
            "last_name": "san",
            "email": "yuki@gmail.com",
            "username": "david124",
            "password": "david123456"
        }
    response = test_client.post(
        url=f"{auth_prefix}/signup",
        json=signup_data
    )

    assert fake_user_service.user_exists_called_once()
    assert fake_user_service.user_exists_called_once_with(signup_data['email'], fake_session)