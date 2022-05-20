from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import CharField, IntegerField, SlugField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import TIME_CASH

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_paginator

User = get_user_model()


@cache_page(TIME_CASH, key_prefix="index_page")
def index(request: HttpRequest) -> HttpResponse:
    """Вернуть HttpResponse объекта главной страницы."""
    posts = Post.objects.select_related("group", "author")
    page_obj = get_paginator(request, posts)
    return render(request, "posts/index.html", {'page_obj': page_obj})


def group_posts(request: HttpRequest, slug: SlugField) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("group", "author")
    page_obj = get_paginator(request, posts)
    context = {"group": group, "page_obj": page_obj}
    return render(request, "posts/group_list.html", context)


def profile(request: HttpRequest, username: CharField) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы профиля."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("author")
    page_obj = get_paginator(request, posts)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    context = {
        "author": author,
        "page_obj": page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: IntegerField) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы деталей поста."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(
        request.POST or None
    )
    # без request.POST or None не проходятся тесты яндекса
    context = {
        "post": post,
        "comments": comments,
        "form": form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы создания поста."""
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
def post_edit(request: HttpRequest, post_id: IntegerField) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы редактирования поста."""
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
def add_comment(request: HttpRequest, post_id: IntegerField) -> HttpResponse:
    """Вернуть HttpResponse объекта добавления комментария."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """Вернуть HttpResponse объекта страницы подписок."""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(request, posts)
    context = {
        "page_obj": page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request: HttpRequest, username: CharField) -> HttpResponse:
    """Вернуть HttpResponse объекта подписки на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user, author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(
    request: HttpRequest,
    username: CharField
) -> HttpResponse:
    """Вернуть HttpResponse объекта отмены подписки на автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author.username)
