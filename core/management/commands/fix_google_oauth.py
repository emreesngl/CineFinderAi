from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApplication
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Google OAuth duplicate kayıtlarını temizler'

    def handle(self, *args, **options):
        self.stdout.write("Google OAuth kayıtları kontrol ediliyor...")
        
        # Tüm Google provider kayıtlarını bul
        google_apps = SocialApplication.objects.filter(provider='google')
        self.stdout.write(f"Bulunan Google OAuth kayıtları: {google_apps.count()}")
        
        if google_apps.count() > 1:
            self.stdout.write(
                self.style.WARNING("Birden fazla Google OAuth kaydı bulundu. Temizleniyor...")
            )
            
            # İlk kaydı hariç diğerlerini sil
            apps_to_delete = google_apps[1:]
            for app in apps_to_delete:
                self.stdout.write(f"Siliniyor: {app.name} (ID: {app.id})")
                app.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f"{len(apps_to_delete)} kayıt silindi.")
            )
        
        # Kalan kayıt varsa kontrol et
        remaining_apps = SocialApplication.objects.filter(provider='google')
        if remaining_apps.exists():
            app = remaining_apps.first()
            self.stdout.write(f"Kalan Google OAuth kaydı: {app.name}")
            
            # Site ile ilişkilendir
            site = Site.objects.get_current()
            if site not in app.sites.all():
                app.sites.add(site)
                self.stdout.write(f"Site ({site.domain}) ile ilişkilendirildi.")
        else:
            self.stdout.write("Google OAuth kaydı bulunamadı. Yeni kayıt oluşturuluyor...")
            
            # Yeni SocialApplication oluştur
            google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
            app_config = google_config.get('APP', {})
            
            if app_config.get('client_id') and app_config.get('secret'):
                app = SocialApplication.objects.create(
                    provider='google',
                    name='Google',
                    client_id=app_config['client_id'],
                    secret=app_config['secret']
                )
                
                site = Site.objects.get_current()
                app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS("Yeni Google OAuth kaydı oluşturuldu ve site ile ilişkilendirildi.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("HATA: Google OAuth ayarları settings.py'da bulunamadı!")
                )

        self.stdout.write(self.style.SUCCESS("İşlem tamamlandı!")) 