from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone # Notification için eklendi
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

class Badge(models.Model):
    CATEGORY_CHOICES = (
        ('rating', 'Puanlama'),           # Puan verme
        ('commenting', 'Yorumlama'),      # Yorum yazma  
        ('collection', 'Koleksiyon'),     # Favori, İzleme Listesi
        ('social', 'Sosyal'),             # Takipçi, Takip etme
        ('community', 'Topluluk'),        # Genel topluluk aktivitesi
        ('special', 'Özel'),              # Diğer
    )
    
    TIER_CHOICES = (
        ('bronze', 'Bronz'),
        ('silver', 'Gümüş'),
        ('gold', 'Altın'),
    )
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Rozet Adı')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    icon = models.ImageField(upload_to='badge_icons/', blank=True, null=True, verbose_name='Rozet İkonu')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='special', verbose_name='Kategori')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze', verbose_name='Seviye')
    tier_order = models.IntegerField(default=1, verbose_name='Seviye Sırası')  # 1=Bronz, 2=Gümüş, 3=Altın
    points_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Puan')
    comment_count_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Yorum Sayısı')
    favorites_count_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Favori Sayısı')
    ratings_count_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Puanlama Sayısı')
    followers_count_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Takipçi Sayısı')
    following_count_required = models.IntegerField(null=True, blank=True, verbose_name='Gereken Takip Sayısı')
    is_active = models.BooleanField(default=True, verbose_name='Aktif mi?')
    # Diğer kazanma koşulları için alanlar eklenebilir (yorum sayısı, izlenen film sayısı vs.)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Rozet'
        verbose_name_plural = 'Rozetler'
        ordering = ['category', 'tier_order', 'name']

class User(AbstractUser):
    bio = models.TextField(blank=True, null=True, verbose_name='Hakkında')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name='Profil Resmi')
    points = models.IntegerField(default=0, verbose_name='Puan')
    level = models.IntegerField(default=1, verbose_name='Seviye')
    badges = models.ManyToManyField(Badge, blank=True, verbose_name='Kazanılan Rozetler')
    # Rozetler için ManyToManyField veya başka bir yapı düşünülebilir, şimdilik basit tutalım.
    # badges = models.ManyToManyField('Badge', blank=True)

    def __str__(self):
        return self.username


class Media(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('movie', 'Film'),
        ('tv', 'Dizi'),
    )
    tmdb_id = models.CharField(max_length=20, unique=True) # TMDB ID (string olabilir)
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Başlık') # Temel bilgi için eklenebilir
    poster_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='Poster Yolu') # Poster path'i saklamak için

    def __str__(self):
        return f"{self.title or self.tmdb_id} ({self.get_media_type_display()})"

    class Meta:
        # tmdb_id ve media_type birlikte benzersiz olmalı
        unique_together = ('tmdb_id', 'media_type')
        ordering = ['title']


class UserList(models.Model):
    # Güncellenmiş liste türleri
    LIST_TYPE_CHOICES = [
        ('favorite', 'Favoriler'),
        ('watchlist', 'İzlenecekler'),
        ('follow', 'Takip Listesi'), # Takip listesi eklendi
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_lists', verbose_name='Kullanıcı')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='listed_by', verbose_name='Medya')
    list_type = models.CharField(max_length=10, choices=LIST_TYPE_CHOICES, verbose_name='Liste Türü')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Eklenme Tarihi')

    class Meta:
        unique_together = ('user', 'media', 'list_type') # Bir kullanıcı bir medyayı bir listeye sadece bir kez ekleyebilir
        verbose_name = 'Kullanıcı Listesi'
        verbose_name_plural = 'Kullanıcı Listeleri'

    def __str__(self):
        return f"{self.user.username} - {self.media} ({self.get_list_type_display()})"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='Kullanıcı')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='comments', verbose_name='Medya')
    content = models.TextField(verbose_name='Yorum İçeriği') # text yerine content kullanıldı (template ile uyum)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Yorum'
        verbose_name_plural = 'Yorumlar'

    def __str__(self):
        return f"{self.user.username} -> {self.media}: {self.content[:50]}..."


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings', verbose_name='Kullanıcı')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='ratings', verbose_name='Medya')
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], verbose_name='Puan (1-10)') # 1-10 arası puan
    rated_at = models.DateTimeField(auto_now_add=True, verbose_name='Puanlama Tarihi')

    class Meta:
        unique_together = ('user', 'media') # Bir kullanıcı bir medyaya sadece bir kez puan verebilir
        verbose_name = 'Puanlama'
        verbose_name_plural = 'Puanlamalar'

    def __str__(self):
        return f"{self.user.username} -> {self.media}: {self.score}/10"


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE, verbose_name='Takip Eden')
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE, verbose_name='Takip Edilen')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Takip Başlangıç Tarihi')

    class Meta:
        unique_together = ('follower', 'followed') # Aynı kullanıcıyı tekrar takip edemez
        ordering = ['-created_at']
        verbose_name = 'Takip'
        verbose_name_plural = 'Takipler'

    def __str__(self):
        return f"{self.follower.username} takip ediyor: {self.followed.username}"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, verbose_name='Gönderen')
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, verbose_name='Alan')
    text = models.TextField(verbose_name='Mesaj Metni')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Gönderilme Tarihi')
    is_read = models.BooleanField(default=False, verbose_name='Okundu mu?')

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Mesaj'
        verbose_name_plural = 'Mesajlar'

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.text[:50]}..."


# Yeni Bildirim Modeli
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='Kullanıcı')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, null=True, blank=True, verbose_name='İlgili Medya')
    message = models.TextField(verbose_name='Bildirim Mesajı')
    is_read = models.BooleanField(default=False, verbose_name='Okundu mu?')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Oluşturulma Tarihi')
    link = models.URLField(blank=True, null=True, verbose_name='Bildirim Linki') # Bildirim tıklanınca gidilecek URL

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}... ({'Okunmadı' if not self.is_read else 'Okundu'})"


# --- Chatbot Geçmişi Modelleri ---

class ChatConversation(models.Model):
    """Kullanıcı ile chatbot arasındaki bir sohbet oturumu."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations', verbose_name='Kullanıcı')
    title = models.CharField(max_length=200, default='Yeni Sohbet', verbose_name='Sohbet Başlığı') # İlk mesajdan otomatik oluşturulabilir
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Başlama Zamanı')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Son Mesaj Zamanı')

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Sohbet Konuşması'
        verbose_name_plural = 'Sohbet Konuşmaları'

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.updated_at.strftime('%d-%m-%Y %H:%M')})"

class ChatMessage(models.Model):
    """Bir sohbet konuşmasındaki tek bir mesaj."""
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages', verbose_name='Konuşma')
    sender_is_user = models.BooleanField(default=True, verbose_name='Gönderen Kullanıcı mı?') # True: Kullanıcı, False: AI
    text = models.TextField(verbose_name='Mesaj İçeriği')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Gönderilme Zamanı')
    recommendations_json = models.JSONField(null=True, blank=True, verbose_name='Öneri Verisi (JSON)') # Afişler için

    class Meta:
        ordering = ['sent_at']
        verbose_name = 'Sohbet Mesajı'
        verbose_name_plural = 'Sohbet Mesajları'

    def __str__(self):
        sender = "Kullanıcı" if self.sender_is_user else "AI"
        return f"{self.conversation.id} - {sender}: {self.text[:50]}..."

# Kullanıcıların gizlediği sohbetleri takip etmek için yeni model
class UserHiddenConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_conversations', verbose_name='Gizleyen Kullanıcı')
    other_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_hidden_by', verbose_name='Sohbetin Diğer Kullanıcısı')
    hidden_at = models.DateTimeField(auto_now_add=True, verbose_name='Gizlenme Zamanı')

    class Meta:
        unique_together = ('user', 'other_user') # Bir kullanıcı bir sohbeti sadece bir kez gizleyebilir
        verbose_name = 'Gizlenen Sohbet'
        verbose_name_plural = 'Gizlenen Sohbetler'
        ordering = ['-hidden_at']

    def __str__(self):
        return f"{self.user.username} gizledi: {self.other_user.username}"
