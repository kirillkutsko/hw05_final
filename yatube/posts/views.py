from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import SlugField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from yatube.settings import TIME_CASH
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from django.views.decorators.cache import cache_page
from .utils import paginator

User = get_user_model()


@cache_page(TIME_CASH, key_prefix="index_page")
def index(request: HttpRequest) -> HttpResponse:
    """Вернуть HttpResponse объекта главной страницы"""
    post_list = Post.objects.select_related("group")
    page_obj = paginator(request, post_list)
    return render(request, "posts/index.html", {'page_obj': page_obj})


def group_posts(request: HttpRequest, slug: SlugField) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы группы"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("group", "author")
    page_obj = paginator(request, post_list)
    context = {"group": group, "page_obj": page_obj}
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("author")
    page_obj = paginator(request, post_list)
    if request.user.is_authenticated and request.user != author:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    else:
        following = False
    context = {
        "author": author,
        "page_obj": page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(
        request.POST or None
    )
    context = {
        "post": post,
        "comments": comments,
        "form": form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post.pk)
    is_edit = True
    context = {
        "form": form,
        "post_id": post_id,
        "is_edit": is_edit,
    }
    return render(
        request,
        "posts/create_post.html",
        context
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post_list)
    context = {
        "page_obj": page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user, author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author.username)
