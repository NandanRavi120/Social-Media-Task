import graphene
from graphene_django import DjangoObjectType # type: ignore
from .models import Comment, Post, User
from datetime import timezone

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"


class Query(graphene.ObjectType):
    comment = graphene.Field(CommentType, id=graphene.Int(required=True))
    allComments = graphene.List(CommentType)

    def resolve_comment(self, info, id):
        try:
            return Comment.objects.get(id=id, deleted_at__isnull=True)
        except Comment.DoesNotExist:
            return None

    def resolve_allComments(self, info):
        return Comment.objects.filter(deleted_at__isnull=True)


class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.Int()

    comment = graphene.Field(CommentType)

    def mutate(self, info, post_id, content, parent_id=None):
        user = info.context.user

        if not user.is_authenticated:
            raise Exception("Authentication required!")

        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                raise Exception("Parent comment not found")
        else:
            parent_comment = None

        comment = Comment.objects.create(user=user, post_id=post_id, content=content, parent=parent_comment)
        return CreateComment(comment=comment)

class UpdateComment(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        content = graphene.String()

    comment = graphene.Field(CommentType)

    def mutate(self, info, id, content):
        user = info.context.user

        try:
            comment = Comment.objects.get(id=id)
        except Comment.DoesNotExist:
            raise Exception("Comment not found")

        if comment.user != user:
            raise Exception("You don't have permission to update this comment")

        if content:
            comment.content = content
            comment.save()

        return UpdateComment(comment=comment)

class DeleteComment(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise Exception("Authentication required!")

        try:
            comment = Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            raise Exception("Comment not found")

        comment.deleted_at = timezone.now()
        comment.save()
        return DeleteComment(success=True)


class Mutation(graphene.ObjectType):
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    delete_comment = DeleteComment.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)


