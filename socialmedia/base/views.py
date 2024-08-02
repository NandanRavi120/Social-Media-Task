from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from .models import User, Post, Comment, Likes, CommentLike
import json

# Create your views here.



# Register View
@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    def get(self, request):
        return JsonResponse({"message": "Get Method not allowed!!!"}, status=400)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error":"Invalid Json"}, status=400)
        
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return JsonResponse({"error": "Name, Email and password are required"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(name=name, email=email, password=password)
        user.save()

        return JsonResponse({"message": "User registered successfully"}, status=201)
    



# Login View
@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    def get(self, request):
        return JsonResponse({"message": "Get Method not allowed!!!"}, status=400)


    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            user = authenticate(email=email, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse({"message": "Login successful"}, status=200)
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=401)
        except Exception as e:
            print("Error during login attempt:", e)
            return JsonResponse({"error": "An error occurred during login"}, status=500)



# Post View
@method_decorator(csrf_exempt, name="dispatch")
class PostView(View):
    def get(self, request, pk=None):
        if request.user.is_authenticated:
            if pk:
                try:
                    post = Post.objects.get(pk=pk)
                    if post.deleted_at:
                        return JsonResponse({"error":"Post Unavailable"}, status=404)
                    if post.hidden_at and post.user != request.user:
                        return JsonResponse({"message":"You are not allowed to view this POST!!"}, status=400)
                    data = {
                        "id": post.id,
                        "note": post.note,
                        "caption": post.caption,
                        "tag": post.tag,
                    }
                    return JsonResponse(data)
                except Post.DoesNotExist:
                    return JsonResponse({"error": "Post not Present"}, status=404)
            else:
                posts = Post.objects.filter(deleted_at=None).exclude(hidden_at__isnull=False).union(
                    Post.objects.filter(deleted_at=None, user=request.user, hidden_at__isnull=False)
                )
                data = [{"id": post.id, "note": post.note, "caption": post.caption, "tag": post.tag} for post in posts]
                return JsonResponse(data, safe=False)
        else:
            if pk:
                try:
                    post = Post.objects.get(pk=pk)
                    if post.hidden_at or post.deleted_at:
                        return JsonResponse({"error":"Post Unavailable"}, status=404)
                    data = {
                        "id": post.id,
                        "note": post.note,
                        "caption": post.caption,
                        "tag": post.tag,
                    }
                    return JsonResponse(data)
                except Post.DoesNotExist:
                    return JsonResponse({"error": "Post not Present"}, status=404)
            else:
                posts = Post.objects.filter(hidden_at=None, deleted_at=None)
                data = [{"id": post.id, "note": post.note, "caption": post.caption, "tag": post.tag} for post in posts]
                return JsonResponse(data, safe=False)

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        note = data.get("note")
        caption = data.get("caption")
        tag = data.get("tag")

        if pk:
            try:
                post = Post.objects.get(pk=pk)
                if post.user != request.user:
                    return JsonResponse({"message":"You are not allowed to Edit this POST!!"}, status=400)
                post.note = note
                post.caption = caption
                post.tag = tag
                post.save()
                return JsonResponse({"status": "success", "post_id": post.id})
            except Exception as e:
                return JsonResponse({"status": "error", "message": e}, status=400)
        else:
            try:
                post = Post.objects.create(user=request.user, note=note, caption=caption, tag=tag)
                context = {"POST Id":post.id}
                return JsonResponse({"status": "Post Uploaded Successfully", "Uploaded_Item":context}, status=201)
            except Exception as e:
                return JsonResponse({"status": "error", "message" : e}, status=400)

    def put(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        if pk is None:
            return JsonResponse({"message":"Enter data which you want to make Private!!"}, status=400)
        try:
            post = Post.objects.get(pk=pk)
            post.hidden_at = timezone.now()
            post.save()
            return JsonResponse({"message":"Hidden Successfully!!"}, status=200)
        except Exception as e:
            return JsonResponse({"error":e})

    def delete(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        if pk is None:
            return JsonResponse({"message":"Enter data which you want to delete!!"}, status=400)
        try:
            post = Post.objects.get(pk=pk)
            post.deleted_at = timezone.now()
            post.save()
            return JsonResponse({"message":"Deleted Successfully!!"}, status=200)
        except Post.DoesNotExist:
            return JsonResponse({"error":"Post Not Found"}, status=404)



@method_decorator(csrf_exempt, name="dispatch")
class PostLikesView(View):
    def get(self, request, pk=None):
        try:
            if pk:
                try:
                    post = Post.objects.get(pk=pk)
                    if post.deleted_at:
                        return JsonResponse({"error": "Post Unavailable"}, status=404)
                    count = Likes.objects.filter(post=pk, deleted_at=None).count()
                    return JsonResponse({"count": count}, status=200)
                except Post.DoesNotExist:
                    return JsonResponse({"error": "Post not Present"}, status=404)
        except Exception as e:
            return JsonResponse({"message":"Invalid Data"}, status=400)
    # Multiple Likes in Post by User
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        try:
            post = Post.objects.get(id=pk)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)
        user = request.user
        created_like = Likes.objects.create(post=post, user=user)
        return JsonResponse({"message":"Like Added"}, status=200)

    # Single Like in Post by User
    # def post(self, request, pk=None):
        # if not request.user.is_authenticated:
        #     return JsonResponse({"error": "Login First"}, status=401)
    #     if pk:
    #         try:
    #             post = Post.objects.get(pk=pk)
    #             if post.deleted_at:
    #                 return JsonResponse({"error": "Post Unavailable"}, status=404)
    #             user = request.user.id
    #             try:
    #                 like = Likes.objects.get(user_id=user, post=post, deleted_at=None)
    #                 if like.deleted_at is None:
    #                     like.deleted_at = timezone.now()
    #                     message = "Like Removed"
    #                 like.save()
    #             except Likes.DoesNotExist:
    #                 like = Likes.objects.create(user_id=user, post=post)
    #                 message = "Like Added"
    #             return JsonResponse({"message": message}, status=200)
    #         except Post.DoesNotExist:
    #             return JsonResponse({"error": "Post not Present"}, status=404)




@method_decorator(csrf_exempt, name="dispatch")
class CommentsView(View):
    def get(self, request, pk=None):
        if pk:
            comments = Comment.objects.filter(pk=pk, deleted_at=None)
        else:
            comments = Comment.objects.filter(deleted_at=None)

        comment_data = []
        for comment in comments:
            comment_data.append({
                "id": comment.id,
                "post": comment.post.id,
                "content": comment.content,
                "parent": comment.parent.id if comment.parent else None,
                "user": comment.user.name
            })

        return JsonResponse({"comments": comment_data})

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
            post_id = data.get("post")
            content = data.get("content")
            parent_id = data.get("parent")

            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    return JsonResponse({"error": "Parent comment not found"}, status=404)
            else:
                parent_comment = None

            comment = Comment.objects.create(user=request.user, post_id=post_id, content=content, parent=parent_comment)
            response_data = {
                "message": "Success!!",
                "id": comment.id,
                "post": comment.post.id, 
                "content": comment.content,
                "parent": comment.parent.id if comment.parent else None
            }
            return JsonResponse(response_data, status=201)
        except Exception as e:
            return JsonResponse({"error":"Something went wrong!!"}, status=400)
    
    def put(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        try:
            comment = Comment.objects.get(id=pk)
        except Comment.DoesNotExist:
            return JsonResponse({"error": "Comment not found"}, status=404)

        if comment.user != request.user:
            return JsonResponse({"error": "You don't have permission to update this comment"}, status=403)

        content = data.get("content")
        if content:
            comment.content = content
            comment.save()

        response_data = {
            "message": "Comment updated successfully",
            "id": comment.id,
            "post": comment.post.id,
            "content": comment.content,
            "parent": comment.parent.id if comment.parent else None
        }
        return JsonResponse(response_data, status=200)

    def delete(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        if pk is None:
            return JsonResponse({"message":"Enter data which you want to delete!!"}, status=400)
        try:
            comment = Comment.objects.get(pk=pk)
            comment.deleted_at = timezone.now()
            comment.save()
            return JsonResponse({"message":"Deleted Successfully!!"}, status=200)
        except Post.DoesNotExist:
            return JsonResponse({"error":"Post Not Found"}, status=404)

@method_decorator(csrf_exempt, name="dispatch")
class CommentLikesView(View):
    def get(self, request, pk=None):
        try:
            if pk:
                try:
                    commentlike = Comment.objects.get(pk=pk)
                    print(commentlike)
                    if commentlike.deleted_at:
                        return JsonResponse({"error": "Comment Unavailable"}, status=404)
                    count = CommentLike.objects.filter(comment=pk, deleted_at=None).count()
                    return JsonResponse({"Comment_id":commentlike.id, "Like Counts": count}, status=200)
                except Comment.DoesNotExist:
                    return JsonResponse({"error": "Comment not Present"}, status=404)
        except Exception as e:
            return JsonResponse({"message":"Invalid Data"}, status=400)

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        if pk:
            try:
                comment = Comment.objects.get(pk=pk)
                if comment.deleted_at:
                    return JsonResponse({"error": "Comment Unavailable"}, status=404)
                user = request.user.id
                try:
                    like = CommentLike.objects.get(user_id=user, comment=comment, deleted_at=None)
                    if like.deleted_at is None:
                        like.deleted_at = timezone.now()
                        message = "Like Removed"
                    like.save()
                except CommentLike.DoesNotExist:
                    like = CommentLike.objects.create(user_id=user, comment=comment)
                    message = "Like Added"
                return JsonResponse({"message": message}, status=200)
            except Comment.DoesNotExist:
                return JsonResponse({"error": "Comment not Present"}, status=404)






@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    def get(self, request):
        return JsonResponse({"message": "Get Method not allowed!!!"}, status=400)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Please Login!!!"}, status=401)

        logout(request)
        return JsonResponse({"message": "Logged out successfully"}, status=200)

