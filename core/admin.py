from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Media, UserList, Comment, Rating, Follow, Message, Badge

# Register your models here.

# Özel User modelini admin paneline kaydedin
admin.site.register(User, UserAdmin)

# Diğer modelleri admin paneline kaydedin
@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tmdb_id', 'media_type', 'title')
    search_fields = ('tmdb_id', 'title')
    list_filter = ('media_type',)

@admin.register(UserList)
class UserListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media', 'list_type', 'added_at')
    list_filter = ('list_type', 'user')
    search_fields = ('user__username', 'media__title', 'media__tmdb_id')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media', 'text_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'media__title', 'text')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Yorum Başlangıcı'

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media', 'score', 'rated_at')
    list_filter = ('score', 'user')
    search_fields = ('user__username', 'media__title')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'followed', 'created_at')
    search_fields = ('follower__username', 'followed__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'text_preview', 'sent_at', 'is_read')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender__username', 'receiver__username', 'text')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Mesaj Başlangıcı'

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'description', 'points_required', 'comment_count_required')
    search_fields = ('name', 'description')
    list_filter = ('category', 'points_required', 'comment_count_required')
