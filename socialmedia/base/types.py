import graphene # type: ignore
from graphene_django import DjangoObjectType # type: ignore
from .models import Comment, CommentLike, Post

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

# Custom PageInfoType for pagination
class PageInfoType(graphene.ObjectType):
    page = graphene.Field(graphene.Int)
    total_pages = graphene.Field(graphene.Int)
    has_next_page = graphene.Field(graphene.Boolean)
    has_previous_page = graphene.Field(graphene.Boolean)

class AllPostsType(graphene.ObjectType):
    posts = graphene.List(PostType)
    page_info = graphene.Field(PageInfoType)
