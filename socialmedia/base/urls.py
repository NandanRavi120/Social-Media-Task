from django.urls import path
from .views import AssignRoleView, RegisterView, LoginView, PostView, LogoutView, PostLikesView, CommentsView, CommentLikesView


urlpatterns = [
    path('assign-role/', AssignRoleView.as_view(), name='assign_role'),
    path("register/", RegisterView.as_view(), name='register'),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("posts/", PostView.as_view(), name="posts"),
    path("posts/<int:pk>/", PostView.as_view(), name="post"),
    path('likes/<int:pk>/', PostLikesView.as_view(), name='post_likes'),
    path('likes/', PostLikesView.as_view(), name='post_likes'),
    path('comments/', CommentsView.as_view(), name='comments'),
    path('comments/<int:pk>/', CommentsView.as_view(), name='comment'),
    path("comment-likes/<int:pk>/", CommentLikesView.as_view(), name="comment_likes"),

]
