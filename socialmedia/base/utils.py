# jwt_utils.py
import jwt, re
from django.conf import settings
from .models import User, Comment, Post
from datetime import datetime, timedelta

def encode_jwt(user):
    expiration_time = datetime.now() + timedelta(minutes=1)
    payload = {
        'user_id': user.id,
        'exp': expiration_time.timestamp()
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM)
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        return user
    except jwt.ExpiredSignatureError:
        return None
    except (jwt.InvalidTokenError, User.DoesNotExist) as e:
        print(e)


# Utility functions
def validate_email(email):
    email_regex = r"^[a-zA-Z][\w._]+@(gmail|yahoo|myyahoo)\.(com|in)$"
    return re.match(email_regex, email)

def get_post(pk):
    try:
        return Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        raise Exception("Post not found")

def get_comment(pk):
    try:
        return Comment.objects.get(pk=pk)
    except Comment.DoesNotExist:
        raise Exception("Comment not found")