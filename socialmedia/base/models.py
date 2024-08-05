from django.contrib.auth.models import AbstractUser
from django.db import models
from .manager import UserManager


# User will be created
class User(AbstractUser):
    name = models.CharField(max_length=30)
    email = models.EmailField(max_length=100, unique=True)
    username = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "Users"
        ordering = ["id"]
        indexes = [models.Index(fields=["email"])]


class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('non-admin', 'Non-Admin'),
    ]
    roles = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "Roles"


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "UserRoles"


class UserRoleLog(models.Model):
    user_role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "UserRoleLogs"



class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    caption = models.TextField()
    tag = models.JSONField()
    hidden_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.note

    class Meta:
        db_table = "Posts"
        ordering = ["id"]
        indexes = [models.Index(fields=["id"])]


class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    counter = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "Likes"




class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="comments", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.content[:10]

    class Meta:
        db_table = "Comments"
        ordering = ["id"]
        indexes = [models.Index(fields=["id", "parent"])]


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="comment_likes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user.name} liked {self.comment.content[:10]}"

    class Meta:
        db_table = "Comment_Likes"
        ordering = ["id"]
        indexes = [models.Index(fields=["id", "comment"])]



