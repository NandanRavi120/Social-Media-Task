class AuthenticatedRequired:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            user = args[1].context.user
            if not user.is_authenticated:
                raise Exception("Authentication required!")
            return func(*args, **kwargs)
        return wrapper
