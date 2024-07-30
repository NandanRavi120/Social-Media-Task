from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager
# Create your models here.

class User(AbstractUser):
    name = models.CharField(max_length=30)
    email = models.EmailField(max_length=100, unique=True)
    username = None
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['name']
    objects=UserManager()
    def __str__(self):
        return self.email
    class Meta:
        ordering = ['id']
