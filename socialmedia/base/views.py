from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.timesince import timesince
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from .models import User, Post, Comment, Likes, CommentLike, Role, UserRole, UserRoleLog
from .utils import encode_jwt
import json, re, requests

# Create your views here.

# AssignRole
@method_decorator(csrf_exempt, name="dispatch")
class AssignRoleView(View):
    def post(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied("You are not authorized to assign roles.")
        
        data = json.loads(request.body)
        user_id = data.get('user_id')
        role_name = data.get('role')
        
        try:
            user = User.objects.get(pk=user_id)
            role = Role.objects.get(roles=role_name)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Role.DoesNotExist:
            return JsonResponse({'error': 'Role not found'}, status=404)
        
        user_role = UserRole.objects.create(user=user, role=role)
        UserRoleLog.objects.create(user_role=user_role, status='active')
        
        return JsonResponse({'message': 'Role assigned successfully'}, status=201)
    
    def put(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied("You are not authorized to change role status.")
        
        data = json.loads(request.body)
        user_role_id = data.get('user_role_id')
        new_status = data.get('status')
        
        try:
            user_role = UserRole.objects.get(pk=user_role_id)
        except UserRole.DoesNotExist:
            return JsonResponse({'error': 'UserRole not found'}, status=404)
        
        user_role_log = UserRoleLog.objects.create(user_role=user_role, status=new_status)
        return JsonResponse({'message': 'Role status updated successfully'}, status=200)


# Register View
@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    def get(self, request):
        return JsonResponse({"message": "Get Method not allowed!!!"}, status=400)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        role = data.get("role", "non-admin")

        email_regex = r"^[a-zA-Z][\w._]+@(gmail|yahoo|myyahoo)\.(com|in)$"
        if not re.match(email_regex, email):
            return JsonResponse({"error":"Email should be from gmail, yahoo, myyahoo and domain should be .com or .in"}, status=400)

        if not name or not email or not password or not phone:
            return JsonResponse({"error": "Name, Email, Mobile and Password are required"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        if role not in ["admin", "non-admin"]:
            return JsonResponse({"error": "Invalid role"}, status=400)

        user = User.objects.create_user(name=name, email=email, mobile_number=phone, password=password)
        user.save()

        role_instance = Role.objects.create(roles=role)
        role_instance.save()

        UserRole.objects.create(user=user, role=role_instance)
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
                token = encode_jwt(user)
                login(request, user)
                return JsonResponse({"message": "Login successful", "token":token}, status=200)
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=401)
        except Exception as e:
            print("Error during login attempt:", e)
            return JsonResponse({"error": "An error occurred during login"}, status=500)


# Post View
@method_decorator(csrf_exempt, name="dispatch")
class PostView(View):
    def get_post_data(self, post):
        data = {
            "id": post.id,
            "user": post.user.id,
            "note": post.note,
            "caption": post.caption,
            "tag": post.tag,
            "created_at": timesince(post.created_at) + "ago",
            "likes": post.likes_set.count(),
            "comments": self.get_comments(post),
        }
        return data

    def get_comments(self, post):
        return [
            {
                "id": comment.id,
                "user": comment.user.id,
                "content": comment.content,
                "created_at": timesince(comment.created_at) + "ago",
                "likes": comment.comment_likes.count(),
                "replies": self.get_replies(comment),
            }
            for comment in Comment.objects.filter(post=post, deleted_at=None)
        ]

    def get_replies(self, comment):
        return [
            {
                "id": reply.id,
                "user": reply.user.id,
                "content": reply.content,
                "created_at": timesince(reply.created_at) + "ago",
                "likes": reply.comment_likes.count(),
            }
            for reply in Comment.objects.filter(parent=comment, deleted_at=None)
        ]

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            posts = Post.objects.filter(hidden_at=None, deleted_at=None)
        else:
            posts = Post.objects.filter(deleted_at=None).exclude(hidden_at__isnull=False)

        if pk:
            try:
                post = posts.get(pk=pk)
                return JsonResponse(self.get_post_data(post))
            except Post.DoesNotExist:
                return JsonResponse({"error": "Post not Present"}, status=404)
        else:
            paginator = Paginator(posts, 20)
            page_number = request.GET.get("page")
            page_objects = paginator.get_page(page_number)
            data = [self.get_post_data(post) for post in page_objects]
            return JsonResponse(data, safe=False)

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        action = data.get("action")
        note = data.get("note")
        caption = data.get("caption")
        tag = data.get("tag")

        if action == "hide":
            if pk is None:
                return JsonResponse({"message": "Enter data which you want to make Private!!"}, status=400)
            try:
                post = Post.objects.get(pk=pk)
                post.hidden_at = timezone.now()
                post.save()
                return JsonResponse({"message": "Hidden Successfully!!"}, status=200)
            except Exception as e:
                return JsonResponse({"error": e})
        
        elif action == "create":
            try:
                post = Post.objects.create(user=request.user, note=note, caption=caption, tag=tag)
                context = {"POST Id": post.id, "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S")}
                return JsonResponse({"status": "Post Uploaded Successfully", "Uploaded_Item": context}, status=201)
            except Exception as e:
                return JsonResponse({"status": "error", "message": e}, status=400)
        elif action == "edit":
            if pk is None:
                return JsonResponse({"message": "Enter post id to edit!!"}, status=400)
            try:
                post = Post.objects.get(pk=pk)
                if post.user != request.user:
                    return JsonResponse({"message": "You are not allowed to Edit this POST!!"}, status=400)
                post.note = note
                post.caption = caption
                post.tag = tag
                post.save()
                return JsonResponse({"status": "success", "post_id": post.id})
            except Exception as e:
                return JsonResponse({"status": "error", "message": e}, status=400)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

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


# Post Like View
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
            else:
                return JsonResponse({"error":"Enter Post to check Likes!!!"}, status=404)
        except Exception as e:
            return JsonResponse({"message":"Invalid Data"}, status=400)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)
        data = json.loads(request.body)
        like_type = data.get("like_type")
        if like_type == "multiplelike":
            return self.multiple_likes(request, data)
        elif like_type == "singlelike":
            return self.single_like(request, data.get("post_id"))
        else:
            return JsonResponse({"error": "An error occurred"}, status=400)

    def multiple_likes(self, request, data):
        pk = data.get("post_id")
        try:
            post = Post.objects.get(id=pk)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
        user = request.user
        like, created = Likes.objects.get_or_create(post=post, user=user, defaults={"counter": 1})
        if not created:
            like.counter += 1
        like.save()
        return JsonResponse({"message": "Like Added", "counter": like.counter}, status=200)

    def single_like(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not Present"}, status=404)
        user = request.user
        like, created = Likes.objects.get_or_create(user=user, post=post, defaults={"deleted_at": None})
        if created:
            message = "Like Added"
        else:
            like.deleted_at = timezone.now() if like.deleted_at is None else None
            message = "Like Removed" if like.deleted_at else "Like Added"
        like.save()
        return JsonResponse({"message": message}, status=200)


# Comment View
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

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login First"}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if pk is None:
            return self.create_comment(request, data)
        else:
            return self.update_comment(request, pk, data)

    def create_comment(self, request, data):
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

    def update_comment(self, request, pk, data):
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


# Comment Like View
@method_decorator(csrf_exempt, name="dispatch")
class CommentLikesView(View):
    def get(self, request, pk=None):
        try:
            if pk:
                try:
                    commentlike = Comment.objects.get(pk=pk)
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


# Logout View
@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    def get(self, request):
        return JsonResponse({"message": "Get Method not allowed!!!"}, status=400)

    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"error": "Please Login!!!"}, status=401)

            logout(request)
            return JsonResponse({"message": "Logged out successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"message":e}, status=400)



@method_decorator(csrf_exempt, name="dispatch")
class ReceiveFromFlaskView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        response_data = {
            'received': data,
            'status': 'success'
        }
        print(response_data)
        user_id = data.get("user")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        note = data.get("note")
        caption = data.get("caption")
        tag = data.get("tag")
        Post.objects.create(user=user, note=note, caption=caption, tag=tag)
        return JsonResponse(response_data, status=200)
