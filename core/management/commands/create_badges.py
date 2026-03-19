from django.core.management.base import BaseCommand
from core.models import Badge


class Command(BaseCommand):
    help = 'Tüm rozet sistemini oluşturur'

    def handle(self, *args, **options):
        badges_data = [
            # PUANLAMA KATEGORİSİ
            {
                'name': 'İlk Adım',
                'description': 'İlk kez bir filme veya diziye puan verdin!',
                'category': 'rating',
                'tier': 'bronze',
                'tier_order': 1,
                'ratings_count_required': 1,
                'icon_emoji': '⭐'
            },
            {
                'name': 'Aktif Puanlayıcı',
                'description': '10 farklı filme/diziye puan verdin.',
                'category': 'rating',
                'tier': 'silver',
                'tier_order': 2,
                'ratings_count_required': 10,
                'icon_emoji': '🌟'
            },
            {
                'name': 'Puanlama Uzmanı',
                'description': '50 farklı filme/diziye puan verdin. Sen gerçek bir uzman olmuşsun!',
                'category': 'rating',
                'tier': 'gold',
                'tier_order': 3,
                'ratings_count_required': 50,
                'icon_emoji': '💫'
            },
            
            # YORUMLAMA KATEGORİSİ
            {
                'name': 'İlk Yorum',
                'description': 'İlk yorumunu yazdın ve topluluğa katıldın!',
                'category': 'commenting',
                'tier': 'bronze',
                'tier_order': 1,
                'comment_count_required': 1,
                'icon_emoji': '💬'
            },
            {
                'name': 'Yorumcu',
                'description': '10 yorum yazarak fikirlerini paylaştın.',
                'category': 'commenting',
                'tier': 'silver',
                'tier_order': 2,
                'comment_count_required': 10,
                'icon_emoji': '🗨️'
            },
            {
                'name': 'Eleştirmen',
                'description': '25 yorumla gerçek bir film eleştirmeni oldun!',
                'category': 'commenting',
                'tier': 'gold',
                'tier_order': 3,
                'comment_count_required': 25,
                'icon_emoji': '🎭'
            },
            
            # KOLEKSİYON KATEGORİSİ
            {
                'name': 'İlk Favori',
                'description': 'İlk favorini ekledin ve koleksiyonunu başlattın!',
                'category': 'collection',
                'tier': 'bronze',
                'tier_order': 1,
                'favorites_count_required': 1,
                'icon_emoji': '❤️'
            },
            {
                'name': 'Koleksiyoncu',
                'description': '10 favori ekleyerek güzel bir koleksiyon oluşturdun.',
                'category': 'collection',
                'tier': 'silver',
                'tier_order': 2,
                'favorites_count_required': 10,
                'icon_emoji': '💖'
            },
            {
                'name': 'Arşivci',
                'description': '25 favori! Sen gerçek bir film/dizi arşivcisisn.',
                'category': 'collection',
                'tier': 'gold',
                'tier_order': 3,
                'favorites_count_required': 25,
                'icon_emoji': '📚'
            },
            
            # SOSYAL KATEGORİSİ
            {
                'name': 'İlk Takipçi',
                'description': 'İlk takipçini kazandın! Popülerliğe giden yolda ilk adım.',
                'category': 'social',
                'tier': 'bronze',
                'tier_order': 1,
                'followers_count_required': 1,
                'icon_emoji': '👤'
            },
            {
                'name': 'Popüler',
                'description': '5 takipçiye ulaştın. İnsanlar seni takip etmeye başladı!',
                'category': 'social',
                'tier': 'silver',
                'tier_order': 2,
                'followers_count_required': 5,
                'icon_emoji': '👥'
            },
            {
                'name': 'Ünlü',
                'description': '10 takipçi! Sen artık bir mikro-ünlüsün.',
                'category': 'social',
                'tier': 'gold',
                'tier_order': 3,
                'followers_count_required': 10,
                'icon_emoji': '🌟'
            },
            
            {
                'name': 'Sosyal',
                'description': 'İlk kişiyi takip ettin ve sosyal olmaya başladın!',
                'category': 'social',
                'tier': 'bronze',
                'tier_order': 1,
                'following_count_required': 1,
                'icon_emoji': '🤝'
            },
            {
                'name': 'Ağ Kurucu',
                'description': '5 kişiyi takip ederek sosyal ağını genişlettın.',
                'category': 'social',
                'tier': 'silver',
                'tier_order': 2,
                'following_count_required': 5,
                'icon_emoji': '🔗'
            },
            {
                'name': 'Topluluk Lideri',
                'description': '10 kişiyi takip ediyorsun. Gerçek bir topluluk liderisin!',
                'category': 'social',
                'tier': 'gold',
                'tier_order': 3,
                'following_count_required': 10,
                'icon_emoji': '👑'
            },
            
            # TOPLULUK KATEGORİSİ
            {
                'name': 'Yeni Üye',
                'description': 'Topluluğumuza hoş geldin! İlk 50 puanını kazandın.',
                'category': 'community',
                'tier': 'bronze',
                'tier_order': 1,
                'points_required': 50,
                'icon_emoji': '🎬'
            },
            {
                'name': 'Aktif Üye',
                'description': '100 puana ulaştın ve aktif bir topluluk üyesi oldun.',
                'category': 'community',
                'tier': 'silver',
                'tier_order': 2,
                'points_required': 100,
                'icon_emoji': '🎪'
            },
            {
                'name': 'Film Gurmesi',
                'description': '250 puan! Sen gerçek bir sinema tutkunusun.',
                'category': 'community',
                'tier': 'gold',
                'tier_order': 3,
                'points_required': 250,
                'icon_emoji': '🏆'
            },
            
            # ÖZEL KATEGORİSİ
            {
                'name': 'Erken Keşif',
                'description': 'Henüz çok bilinmeyen yapıları keşfediyorsun.',
                'category': 'special',
                'tier': 'bronze',
                'tier_order': 1,
                'points_required': 10,
                'icon_emoji': '🔍'
            },
            {
                'name': 'Trend Yakalayıcı',
                'description': 'Popüler olmaya başlayan yapıları erkenden keşfediyorsun.',
                'category': 'special',
                'tier': 'silver',
                'tier_order': 2,
                'points_required': 75,
                'icon_emoji': '📈'
            },
            {
                'name': 'Sinema Efsanesi',
                'description': 'FilmBot topluluğunun efsanevi üyelerinden birisin!',
                'category': 'special',
                'tier': 'gold',
                'tier_order': 3,
                'points_required': 500,
                'icon_emoji': '👑'
            }
        ]

        created_count = 0
        updated_count = 0

        for badge_data in badges_data:
            icon_emoji = badge_data.pop('icon_emoji', '🏅')
            
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults={
                    **badge_data,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Yeni rozet oluşturuldu: {badge.name} ({icon_emoji})')
                )
            else:
                # Mevcut rozeti güncelle
                for key, value in badge_data.items():
                    setattr(badge, key, value)
                badge.is_active = True
                badge.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Rozet güncellendi: {badge.name} ({icon_emoji})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Rozet sistemi hazır! '
                f'{created_count} yeni rozet oluşturuldu, '
                f'{updated_count} rozet güncellendi.'
            )
        ) 