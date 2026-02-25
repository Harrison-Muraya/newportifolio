from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import GalleryImage, ImageLike, ImageComment, ContactMessage


class ImageCommentInline(admin.TabularInline):
    model = ImageComment
    extra = 0
    readonly_fields = ('user', 'text', 'created_at')


class ImageLikeInline(admin.TabularInline):
    model = ImageLike
    extra = 0
    readonly_fields = ('user', 'created_at')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'thumbnail', 'like_count', 'comment_count', 'uploaded_at')
    list_filter = ('category', 'uploaded_at')
    search_fields = ('title', 'description')
    inlines = [ImageCommentInline, ImageLikeInline]

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px;" />', obj.image.url)
        return '-'
    thumbnail.short_description = 'Preview'

    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = '❤️ Likes'

    def comment_count(self, obj):
        return obj.comment_count()
    comment_count.short_description = '💬 Comments'


@admin.register(ImageComment)
class ImageCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')

    def short_text(self, obj):
        return obj.text[:80]
    short_text.short_description = 'Comment'


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('display_name_col', 'display_email_col', 'short_message', 'sent_at', 'is_read_badge')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('name', 'email', 'message', 'sender__username')
    readonly_fields = ('sender', 'email', 'name', 'message', 'sent_at', 'chat_bubble')
    actions = ['mark_as_read', 'mark_as_unread']

    def display_name_col(self, obj):
        return obj.display_name
    display_name_col.short_description = 'From'

    def display_email_col(self, obj):
        email = obj.display_email
        if email and email != 'No email provided':
            return format_html('<a href="mailto:{}">{}</a>', email, email)
        return format_html('<span style="color:#999;">No email</span>')
    display_email_col.short_description = 'Email'

    def short_message(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    short_message.short_description = 'Message'

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="background:#10b981;color:white;padding:2px 10px;border-radius:20px;font-size:12px;">Read</span>')
        return format_html('<span style="background:#f59e0b;color:white;padding:2px 10px;border-radius:20px;font-size:12px;">New</span>')
    is_read_badge.short_description = 'Status'

    def chat_bubble(self, obj):
        avatar_letter = obj.display_name[0].upper()
        time_str = obj.sent_at.strftime('%B %d, %Y at %I:%M %p')
        email_str = obj.display_email
        return mark_safe(f"""
        <div style="
            max-width: 700px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        ">
            <div style="
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 20px;
                background: linear-gradient(135deg, #f0f4ff 0%, #f8f0ff 100%);
                border-radius: 16px;
                border-left: 4px solid #667eea;
                box-shadow: 0 4px 20px rgba(102,126,234,0.1);
                margin: 10px 0;
            ">
                <div style="
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    flex-shrink: 0;
                ">{avatar_letter}</div>
                <div style="flex: 1;">
                    <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <strong style="color: #1a1a2e; font-size: 16px;">{obj.display_name}</strong>
                        <span style="color: #888; font-size: 12px;">📅 {time_str}</span>
                    </div>
                    <div style="color: #555; font-size: 13px; margin-bottom: 10px;">📧 {email_str}</div>
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 16px;
                        color: #333;
                        font-size: 15px;
                        line-height: 1.7;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                        white-space: pre-wrap;
                    ">{obj.message}</div>
                </div>
            </div>
        </div>
        """)
    chat_bubble.short_description = 'Message Preview'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().change_view(request, object_id, form_url, extra_context)

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = 'Mark selected as unread'

    class Media:
        css = {
            'all': []
        }


admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.site_header = "Harrison Muraya Portfolio Admin"
admin.site.site_title = "HM Admin"
admin.site.index_title = "Welcome, Harrison 👋"

