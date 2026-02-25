from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import GalleryImage, ImageLike, ImageComment, ContactMessage, Project
import json


def home(request):
    gallery_images = GalleryImage.objects.all()
    projects = Project.objects.all()
    return render(request, 'harrison/home.html', {'gallery_images': gallery_images, 'projects': projects})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'harrison/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not username or not password1:
            messages.error(request, 'Username and password are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('home')
    
    return render(request, 'harrison/register.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def upload_image(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'projects')
        image_file = request.FILES.get('image')
        
        if image_file:
            img = GalleryImage.objects.create(
                title=title,
                description=description,
                category=category,
                image=image_file,
                uploaded_by=request.user
            )
            return JsonResponse({
                'success': True,
                'id': img.id,
                'title': img.title,
                'url': img.image.url,
                'category': img.category,
                'description': img.description,
            })
        return JsonResponse({'error': 'No image provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@require_POST
def toggle_like(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    like, created = ImageLike.objects.get_or_create(image=image, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'count': image.like_count()})


@login_required
@require_POST
def add_comment(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    data = json.loads(request.body)
    text = data.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Empty comment'}, status=400)
    
    comment = ImageComment.objects.create(image=image, user=request.user, text=text)
    return JsonResponse({
        'id': comment.id,
        'user': request.user.get_full_name() or request.user.username,
        'text': comment.text,
        'created_at': comment.created_at.strftime('%b %d, %Y'),
    })


def get_image_data(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    comments = [{
        'id': c.id,
        'user': c.user.get_full_name() or c.user.username,
        'text': c.text,
        'created_at': c.created_at.strftime('%b %d, %Y'),
    } for c in image.comments.all()]
    
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ImageLike.objects.filter(image=image, user=request.user).exists()
    
    return JsonResponse({
        'id': image.id,
        'title': image.title,
        'description': image.description,
        'url': image.image.url,
        'like_count': image.like_count(),
        'user_liked': user_liked,
        'comments': comments,
    })


@require_POST
def send_message(request):
    data = json.loads(request.body)
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    
    msg = ContactMessage(message=message_text)
    
    if request.user.is_authenticated:
        msg.sender = request.user
    else:
        msg.email = data.get('email', '').strip() or None
        msg.name = data.get('name', '').strip() or 'Anonymous'
    
    msg.save()
    return JsonResponse({'success': True})


@login_required
def upload_project_bg(request, project_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        bg_image = request.FILES.get('bg_image')
        if bg_image:
            project.bg_image = bg_image
            project.save()
            return JsonResponse({'success': True, 'url': project.bg_image.url})
        return JsonResponse({'error': 'No image provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)
