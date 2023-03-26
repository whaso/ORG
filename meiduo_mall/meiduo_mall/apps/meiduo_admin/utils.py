

def jwt_response_payload_handler(token, user, request):
    return {
        "token": token,
        "username": user.username,
        "userid": user.id
    }
