# middleware.py
from django.http import JsonResponse
from .utils import decode_jwt

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', None)
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
            user = decode_jwt(token)
            if user:
                request.user = user
            else:
                return JsonResponse({'error': "Invalid Token or Token Expired"}, status=401)
        else:
            request.user = None
        
        response = self.get_response(request)
        return response
