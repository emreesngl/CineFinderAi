from .models import Notification, User, Message
from django.templatetags.static import static

def notifications_context(request):
    if request.user.is_authenticated:
        # Mesaj bildirimleri hariç, sadece takip ve diğer sistem bildirimlerini say
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).exclude(
            message__contains='mesaj gönderdi'  # Mesaj bildirimlerini hariç tut
        ).exclude(
            message__contains='size mesaj'  # Mesaj bildirimlerini hariç tut
        ).exclude(
            message__contains='yeni mesaj'  # Mesaj bildirimlerini hariç tut
        ).count()
    else:
        unread_count = 0
    return {
        'unread_notifications_count': unread_count
    }

def messages_context(request):
    if request.user.is_authenticated:
        unread_message_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    else:
        unread_message_count = 0
    return {
        'unread_message_count': unread_message_count
    }

def user_profile_picture_context(request):
    user_pic_url = static('images/default_avatar.png')
    if request.user.is_authenticated:
        if request.user.profile_picture:
            user_pic_url = request.user.profile_picture.url
    return {
        'user_profile_pic_url': user_pic_url
    } 