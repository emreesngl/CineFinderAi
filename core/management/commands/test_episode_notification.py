from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Media, UserList, Notification
from django.urls import reverse

User = get_user_model()

class Command(BaseCommand):
    help = 'Takip edilen diziler için test bildirimi oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Test edilecek kullanıcı adı')
        parser.add_argument('--series-name', type=str, help='Test dizisi adı', default='Breaking Bad')

    def handle(self, *args, **options):
        username = options.get('username')
        series_name = options.get('series_name')
        
        if not username:
            self.stdout.write(self.style.ERROR('Kullanıcı adı belirtmelisiniz: --username <kullanıcı_adı>'))
            return
            
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Kullanıcı bulunamadı: {username}'))
            return
            
        # Test dizisi oluştur veya bul
        media, created = Media.objects.get_or_create(
            tmdb_id=1396,  # Breaking Bad'in TMDB ID'si
            media_type='tv',
            defaults={
                'title': series_name,
                'poster_path': '/ggFHVNu6YYI5L9pCfOacjizRGt.jpg'
            }
        )
        
        if created:
            self.stdout.write(f'Test dizisi oluşturuldu: {media.title}')
        
        # Kullanıcının bu diziyi takip ettiğinden emin ol
        follow_entry, follow_created = UserList.objects.get_or_create(
            user=user,
            media=media,
            list_type='follow'
        )
        
        if follow_created:
            self.stdout.write(f'{user.username} artık {media.title} dizisini takip ediyor')
        else:
            self.stdout.write(f'{user.username} zaten {media.title} dizisini takip ediyor')
            
        # Yeni bölüm bildirimi oluştur
        media_detail_url = reverse('media_detail', kwargs={
            'media_type': media.media_type,
            'media_id': media.tmdb_id
        })
        
        notification = Notification.objects.create(
            user=user,
            media=media,
            message=f'🎬 {media.title} dizisinin yeni bölümü yayınlandı! Sezon 6, Bölüm 1: "Live Free or Die"',
            link=media_detail_url
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Yeni bölüm bildirimi oluşturuldu!\n'
                f'Kullanıcı: {user.username}\n'
                f'Dizi: {media.title}\n'
                f'Bildirim ID: {notification.id}'
            )
        ) 