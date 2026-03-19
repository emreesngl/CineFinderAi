import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_finder_ai.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Mevcut admin kullanıcısını sil
User.objects.filter(username='admin').delete()

# Yeni admin kullanıcısı oluştur
admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
print(f"Admin kullanıcısı oluşturuldu: {admin_user.username}") 