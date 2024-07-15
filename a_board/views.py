from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PostForm, CommentForm
from .models import Post, Image, Comment
import json
import re

@login_required
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'a_board/post_list.html', {'posts': posts})

@csrf_exempt
@login_required
def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('file')
        image_instance = Image.objects.create(image=image, author=request.user)
        return JsonResponse({'url': image_instance.image.url, 'id': image_instance.id})

@login_required
def post_create(request):
    if not request.user.is_staff:
        messages.warning(request, "You do not have permission to create a post.")
        return redirect('post_list')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            image_ids = json.loads(request.POST.get('image_ids', '[]'))
            post.image_list = image_ids
            post.save()
            Image.objects.filter(id__in=image_ids).update(check_for_upload=True)
            Image.objects.filter(check_for_upload=False).delete()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'a_board/post_form.html', {'form': form, 'post': None})

@login_required
def post_update(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.warning(request, "You are not allowed to edit this post.")
        return redirect('post_list')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            old_image_ids = set(post.image_list)
            post = form.save(commit=False)
            post.author = request.user
            
            content_image_ids = set()
            urls = re.findall(r'!\[image\]\((.*?)\)', post.content)
            for url in urls:
                filename = url.split('/')[-1]
                try:
                    image = Image.objects.get(image='images/' + filename)
                    content_image_ids.add(image.id)
                except Image.DoesNotExist:
                    continue

            to_delete_image_ids = old_image_ids - content_image_ids
            for image_id in to_delete_image_ids:
                try:
                    image = Image.objects.get(id=image_id)
                    image.delete()
                except Image.DoesNotExist:
                    continue
            
            post.image_list = list(content_image_ids)
            post.save()
            Image.objects.filter(id__in=content_image_ids).update(check_for_upload=True)
            Image.objects.filter(check_for_upload=False).delete()
            return redirect('post_list')
    else:
        form = PostForm(instance=post)
    return render(request, 'a_board/post_form.html', {'form': form, 'post': post})

@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.warning(request, "You are not allowed to delete this post.")
        return redirect('post_list')
    post.delete()
    return redirect('post_list')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    comment_form = CommentForm()
    return render(request, 'a_board/post_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('post_detail', post_id=post.id)

@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        messages.warning(request, "You are not allowed to delete this comment.")
        return redirect('post_detail', post_id=post_id)
    comment.delete()
    return redirect('post_detail', post_id=post_id)
