import graphene # type: ignore
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from .models import Comment, CommentLike, User, Role, UserRole, Post, Likes
from .utils import encode_jwt, validate_email, get_post, get_comment
from .types import CommentType, PostType
from .decorators import AuthenticatedRequired

authentication_required = AuthenticatedRequired()

# Register Mutation
class Register(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)
        password = graphene.String(required=True)
        role = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone, password, role="non-admin"):
        if not validate_email(email):
            return Register(success=False, message="Invalid email domain")

        if User.objects.filter(email=email).exists():
            return Register(success=False, message="Email already registered")

        if role not in ["admin", "non-admin"]:
            return Register(success=False, message="Invalid role")

        user = User.objects.create_user(name=name, email=email, mobile_number=phone, password=password)
        role_instance = Role.objects.create(roles=role)
        UserRole.objects.create(user=user, role=role_instance)
        return Register(success=True, message="User registered successfully")

# Login Mutation
class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()

    def mutate(self, info, email, password):
        user = authenticate(email=email, password=password)
        if user:
            token = encode_jwt(user)
            login(info.context, user)
            return Login(success=True, message="Login successful", token=token)
        return Login(success=False, message="Invalid credentials")

# Logout Mutation
class Logout(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    @authentication_required
    def mutate(self, info):
        logout(info.context)
        return Logout(success=True, message="Logged out successfully")

# CreateComment Mutation
class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.Int()

    comment = graphene.Field(CommentType)

    @authentication_required
    def mutate(self, info, post_id, content, parent_id=None):
        user = info.context.user
        parent_comment = get_comment(parent_id) if parent_id else None
        comment = Comment.objects.create(user=user, post_id=post_id, content=content, parent=parent_comment)
        return CreateComment(comment=comment)

# UpdateComment Mutation
class UpdateComment(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        content = graphene.String()

    comment = graphene.Field(CommentType)

    def mutate(self, info, id, content):
        user = info.context.user
        comment = get_comment(id)
        if comment.user != user:
            raise Exception("You don't have permission to update this comment")

        if content:
            comment.content = content
            comment.save()

        return UpdateComment(comment=comment)

# DeleteComment Mutation
class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @authentication_required
    def mutate(self, info, id):
        comment = get_comment(id)
        comment.deleted_at = timezone.now()
        comment.save()
        return DeleteComment(success=True)

# LikeComment Mutation
class LikeComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.Int(required=True)

    message = graphene.String()

    @authentication_required
    def mutate(self, info, comment_id):
        user = info.context.user

        comment = get_comment(comment_id)
        if comment.deleted_at:
            raise Exception("Comment Unavailable")

        try:
            like = CommentLike.objects.get(user=user, comment=comment, deleted_at=None)
            if like.deleted_at is None:
                like.deleted_at = timezone.now()
                message = "Like Removed"
            like.save()
        except CommentLike.DoesNotExist:
            CommentLike.objects.create(user=user, comment=comment)
            message = "Like Added"
        return LikeComment(message=message)

# LikePost Mutation
class LikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        like_type = graphene.String(required=True)  # 'singlelike' or 'multiplelike'

    message = graphene.String()
    counter = graphene.Int()

    @authentication_required
    def mutate(self, info, post_id, like_type):
        user = info.context.user

        post = get_post(post_id)

        if like_type == "multiplelike":
            like, created = Likes.objects.get_or_create(post=post, user=user, defaults={"counter": 1})
            if not created:
                like.counter += 1
            like.save()
            return LikePost(message="Like Added", counter=like.counter)

        if like_type == "singlelike":
            like, created = Likes.objects.get_or_create(user=user, post=post, defaults={"deleted_at": None})
            if created:
                message = "Like Added"
            else:
                like.deleted_at = timezone.now() if like.deleted_at is None else None
                message = "Like Removed" if like.deleted_at else "Like Added"
            like.save()
            return LikePost(message=message, counter=like.counter if not created else 1)

        raise Exception("Invalid like_type")

# CreatePost Mutation
class CreatePost(graphene.Mutation):
    class Arguments:
        note = graphene.String(required=True)
        caption = graphene.String(required=True)
        tag = graphene.JSONString(required=True)

    post = graphene.Field(PostType)

    @authentication_required
    def mutate(self, info, note, caption, tag):
        user = info.context.user

        post = Post.objects.create(user=user, note=note, caption=caption, tag=tag)
        return CreatePost(post=post)

# EditPost Mutation
class EditPost(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        note = graphene.String()
        caption = graphene.String()
        tag = graphene.JSONString()

    post = graphene.Field(PostType)

    def mutate(self, info, id, note=None, caption=None, tag=None):
        user = info.context.user
        post = get_post(id)
        if post.user != user:
            raise Exception("You don't have permission to edit this post")

        if note:
            post.note = note
        if caption:
            post.caption = caption
        if tag:
            post.tag = tag

        post.save()
        return EditPost(post=post)

# HidePost Mutation
class HidePost(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @authentication_required
    def mutate(self, info, id):
        user = info.context.user

        post = get_post(id)
        if post.user != user:
            raise Exception("You don't have permission to hide this post")

        post.hidden_at = timezone.now()
        post.save()
        return HidePost(success=True)

# DeletePost Mutation
class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @authentication_required
    def mutate(self, info, id):
        post = get_post(id)
        post.deleted_at = timezone.now()
        post.save()
        return DeletePost(success=True)

# Combine all mutations
class Mutation(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()
    logout = Logout.Field()
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()
    like_comment = LikeComment.Field()
    like_post = LikePost.Field()
    create_post = CreatePost.Field()
    edit_post = EditPost.Field()
    hide_post = HidePost.Field()
    delete_post = DeletePost.Field()
