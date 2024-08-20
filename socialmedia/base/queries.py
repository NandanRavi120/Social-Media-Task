import graphene# type: ignore
from graphene_django import DjangoObjectType # type: ignore
from graphene import Field, Int, List, Boolean # type: ignore
from django.core.paginator import Paginator
from .models import Comment, CommentLike, Post
from .utils import get_comment
from .types import CommentType, AllPostsType, PostType, PageInfoType



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


# import graphene # type: ignore
# from django.core.paginator import Paginator
# from .models import Comment, Post
# from .types import CommentType, PostType, AllPostsType, PageInfoType

# class Query(graphene.ObjectType):
#     # Query to get all comments
#     all_comments = graphene.List(CommentType)

#     def resolve_all_comments(self, info):
#         return Comment.objects.filter(deleted_at=None)

#     # Query to get comments for a specific post
#     comments_by_post = graphene.List(CommentType, post_id=graphene.Int(required=True))

#     def resolve_comments_by_post(self, info, post_id):
#         return Comment.objects.filter(post_id=post_id, deleted_at=None)

#     # Query to get all posts with pagination
#     all_posts = graphene.Field(AllPostsType, page=graphene.Int(required=True), per_page=graphene.Int(required=True))

#     def resolve_all_posts(self, info, page, per_page):
#         posts = Post.objects.filter(deleted_at=None)
#         paginator = Paginator(posts, per_page)

#         if page > paginator.num_pages:
#             raise Exception("Page out of range")

#         page_info = PageInfoType(
#             page=page,
#             total_pages=paginator.num_pages,
#             has_next_page=page < paginator.num_pages,
#             has_previous_page=page > 1,
#         )
#         posts = paginator.page(page).object_list

#         return AllPostsType(posts=posts, page_info=page_info)

#     # Query to get a specific post by ID
#     post_by_id = graphene.Field(PostType, id=graphene.Int(required=True))

#     def resolve_post_by_id(self, info, id):
#         return Post.objects.get(id=id, deleted_at=None)
