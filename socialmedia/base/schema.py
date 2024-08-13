import graphene, re # type: ignore
from graphene_django import DjangoObjectType # type: ignore
from graphene import Field, Int, List, Boolean # type: ignore
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Comment, CommentLike, User, Role, UserRole, Post, Likes
from .utils import encode_jwt
from .decorators import AuthenticatedRequired


authentication_required = AuthenticatedRequired()

# Existing DjangoObjectTypes
class PostType(DjangoObjectType):
    class Meta:
        model = Post

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"

class CommentLikeType(DjangoObjectType):
    class Meta:
        model = CommentLike
        fields = "__all__"

# PageInfoType for pagination
class PageInfoType(graphene.ObjectType):
    page = Field(Int)
    total_pages = Field(Int)
    has_next_page = Field(Boolean)
    has_previous_page = Field(Boolean)

class AllPostsType(graphene.ObjectType):
    posts = List(PostType)
    page_info = Field(PageInfoType)

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

# Register Mutations
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

# Login Mutations
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

# Logout Mutations
class Logout(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    @authentication_required
    def mutate(self, info):
        user = info.context.user
        # check_user_authenticated(user)
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
        user = info.context.user

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
        user = info.context.user

        post = get_post(id)
        post.deleted_at = timezone.now()
        post.save()
        return DeletePost(success=True)

# Queries
class Query(graphene.ObjectType):
    comment = graphene.Field(CommentType, id=graphene.Int(required=True))
    allComments = graphene.List(CommentType)
    post = graphene.Field(PostType, id=graphene.Int(required=True))
    all_posts = Field(AllPostsType, page=Int(default_value=1), page_size=Int(default_value=20))
    like_count = graphene.Int(comment_id=graphene.Int(required=True))

    def resolve_comment(self, info, id):
        return Comment.objects.filter(id=id, deleted_at__isnull=True).first()

    def resolve_allComments(self, info):
        return Comment.objects.filter(deleted_at__isnull=True)

    def resolve_post(self, info, id):
        return Post.objects.filter(pk=id, deleted_at__isnull=True).first()

    def resolve_all_posts(self, info, page=1, page_size=20):
        if not info.context.user.is_authenticated:
            posts = Post.objects.filter(hidden_at=None, deleted_at=None)
        else:
            posts = Post.objects.filter(deleted_at=None).exclude(hidden_at__isnull=False)

        paginator = Paginator(posts, page_size)

        try:
            paginated_posts = paginator.page(page)
        except Exception as e:
            print({"message": e})
            return None

        return AllPostsType(
            posts=paginated_posts.object_list,
            page_info=PageInfoType(
                page=page,
                total_pages=paginator.num_pages,
                has_next_page=paginated_posts.has_next(),
                has_previous_page=paginated_posts.has_previous(),
            ),
        )

    def resolve_like_count(self, info, comment_id):
        comment = get_comment(comment_id)
        if comment.deleted_at:
            raise Exception("Comment Unavailable")
        return CommentLike.objects.filter(comment=comment, deleted_at=None).count()

# Mutation class that combines all mutations
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

schema = graphene.Schema(query=Query, mutation=Mutation)
