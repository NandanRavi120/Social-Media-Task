# jwt_utils.py
import jwt
from django.conf import settings
from .models import User
from datetime import datetime
from datetime import timedelta

def encode_jwt(user):
    expiration_time = datetime.now() + timedelta(minutes=2)
    payload = {
        'user_id': user.id,
        'expiration_time':expiration_time.isoformat()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithm=["HS256"])
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return None

