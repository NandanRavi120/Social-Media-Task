import faker
from django.core.management.base import BaseCommand
from base.models import User, Post, Likes, Comment, CommentLike

class Command(BaseCommand):
    help = 'Generate fake data for models'

    def handle(self, *args, **kwargs):
        fake = faker.Faker()

        users = []
        for i in range(2):
            print(f"{i} User is added")
            user = User.objects.create_user(name=fake.name(), email=fake.email(), password='password')
            users.append(user)

        posts = []
        for user in users:
            for i in range(10):
                print(f"{i} Post is added")
                post = Post.objects.create(user=user, note=fake.text(), caption=fake.text(), tag={})
                posts.append(post)

        likes = []
        for user in users:
            for post in posts:
                print("Like Added Successfully")
                like = Likes.objects.create(user=user, post=post, counter=fake.random_int(min=1, max=20))
                likes.append(like)

        comments = []
        for user in users:
            for post in posts:
                print("Comment Added Successfully")
                comment = Comment.objects.create(user=user, post=post, content=fake.text(), parent=None)
                comments.append(comment)

        comment_likes = []
        for user in users:
            for comment in comments:
                comment_like = CommentLike.objects.create(user=user, comment=comment)
                comment_likes.append(comment_like)

        self.stdout.write(self.style.SUCCESS('Fake data generated successfully'))