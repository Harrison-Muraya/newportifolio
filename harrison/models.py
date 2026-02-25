from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class GalleryImage(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=50, choices=[
        ('projects', 'Projects'),
        ('workspace', 'Workspace'),
        ('team', 'Team & Events'),
    ], default='projects')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gallery_images')

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()


class ImageLike(models.Model):
    image = models.ForeignKey(GalleryImage, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('image', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.image.title}"


class ImageComment(models.Model):
    image = models.ForeignKey(GalleryImage, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"


class ContactMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Message from {self.display_name} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def display_name(self):
        if self.sender:
            return self.sender.get_full_name() or self.sender.username
        return self.name or 'Anonymous'

    @property
    def display_email(self):
        if self.sender:
            return self.sender.email
        return self.email or 'No email provided'
