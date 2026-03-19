from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Badge, Comment, Rating, UserList, Follow

User = get_user_model()

# Puan ve seviye güncelleme mantığı (varsa)
def update_user_level(user):
    # Basit bir seviye atlama mantığı: Her 100 puanda bir seviye atla
    new_level = (user.points // 100) + 1
    if new_level != user.level:
        user.level = new_level
        # save() çağrısı post_save sinyalini tekrar tetikleyebilir,
        # dikkatli olmak veya update_fields kullanmak gerekebilir.
        # Şimdilik basit tutuyoruz, save() tekrar tetiklemezse sorun olmaz.
        user.save(update_fields=['level']) # Sadece level güncelliyoruz

# Rozet kazanma mantığı
def check_and_award_badges(user):
    current_badges = set(user.badges.filter(is_active=True))
    awarded_new_badge = False

    # Puana göre rozetler
    point_badges = Badge.objects.filter(
        points_required__isnull=False, 
        is_active=True
    ).order_by('points_required')
    for badge in point_badges:
        if user.points >= badge.points_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for points ({badge.points_required})")

    # Yorum sayısına göre rozetler
    comment_count = Comment.objects.filter(user=user).count()
    comment_badges = Badge.objects.filter(
        comment_count_required__isnull=False, 
        is_active=True
    ).order_by('comment_count_required')
    for badge in comment_badges:
        if comment_count >= badge.comment_count_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for comments ({badge.comment_count_required})")

    # Favori sayısına göre rozetler
    favorites_count = UserList.objects.filter(user=user, list_type='favorite').count()
    favorites_badges = Badge.objects.filter(
        favorites_count_required__isnull=False, 
        is_active=True
    ).order_by('favorites_count_required')
    for badge in favorites_badges:
        if favorites_count >= badge.favorites_count_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for favorites ({badge.favorites_count_required})")

    # Puanlama sayısına göre rozetler  
    ratings_count = Rating.objects.filter(user=user).count()
    ratings_badges = Badge.objects.filter(
        ratings_count_required__isnull=False, 
        is_active=True
    ).order_by('ratings_count_required')
    for badge in ratings_badges:
        if ratings_count >= badge.ratings_count_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for ratings ({badge.ratings_count_required})")

    # Takipçi sayısına göre rozetler
    followers_count = user.followers.count()
    followers_badges = Badge.objects.filter(
        followers_count_required__isnull=False, 
        is_active=True
    ).order_by('followers_count_required')
    for badge in followers_badges:
        if followers_count >= badge.followers_count_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for followers ({badge.followers_count_required})")

    # Takip edilen sayısına göre rozetler
    following_count = user.following.count()
    following_badges = Badge.objects.filter(
        following_count_required__isnull=False, 
        is_active=True
    ).order_by('following_count_required')
    for badge in following_badges:
        if following_count >= badge.following_count_required and badge not in current_badges:
            user.badges.add(badge)
            awarded_new_badge = True
            print(f"User {user.username} awarded badge: {badge.name} for following ({badge.following_count_required})")

    return awarded_new_badge

# Kullanıcı puanı değiştiğinde (User modeli kaydedildiğinde) çalışacak sinyal
@receiver(post_save, sender=User)
def user_saved_handler(sender, instance, created, update_fields=None, **kwargs):
    print(f"User saved: {instance.username}, Created: {created}, Updated Fields: {update_fields}")
    # Sadece puan veya seviye güncellendiğinde rozet kontrolü yapabiliriz,
    # veya her save işleminde kontrol edebiliriz.
    # Şimdilik her save sonrası kontrol edelim (level güncellemesi hariç sonsuz döngü olmaması için)
    if update_fields is None or 'points' in update_fields:
        print(f"Checking badges for {instance.username} after save.")
        check_and_award_badges(instance)
        # Seviye güncelleme (rozeti etkileyebilir, rozet kontrolünden sonra yapmak mantıklı olabilir)
        update_user_level(instance)

# Başka aksiyonlar için puan verme ve rozet kontrolü

def update_points_and_check_badges(user, points_to_add):
    user.points += points_to_add
    user.save(update_fields=['points']) # Sadece puanı güncelle, bu user_saved_handler'ı tetikleyecek.
    # user_saved_handler seviye ve rozet kontrolünü yapacak.
    print(f"Updated points for {user.username} by {points_to_add}. New total: {user.points}")

@receiver(post_save, sender=Comment)
def comment_created_handler(sender, instance, created, **kwargs):
    if created:
        print(f"Comment created by {instance.user.username}. Awarding points.")
        update_points_and_check_badges(instance.user, 5) # Yorum için 5 puan

@receiver(post_save, sender=Rating)
def rating_created_or_updated_handler(sender, instance, created, **kwargs):
    points_to_add = 0
    if created:
        points_to_add = 3 # Yeni puanlama için 3 puan
        print(f"Rating created by {instance.user.username}. Awarding points.")
    # else: # Puan güncellendiğinde de puan verilebilir, şimdilik sadece ilk oylamada
    #     points_to_add = 1 # Güncelleme için 1 puan
    if points_to_add > 0:
        update_points_and_check_badges(instance.user, points_to_add)

@receiver(post_save, sender=UserList)
def list_item_added_handler(sender, instance, created, **kwargs):
    if created:
        points_to_add = 1 # Listeye ekleme için 1 puan
        print(f"List item added by {instance.user.username}. Awarding points.")
        update_points_and_check_badges(instance.user, points_to_add)

# Takip işlemleri için rozet kontrolü
@receiver(post_save, sender=Follow)
def follow_created_handler(sender, instance, created, **kwargs):
    if created:
        # Takip eden kişi için rozet kontrolü (following_count)
        print(f"Follow created: {instance.follower.username} -> {instance.followed.username}")
        check_and_award_badges(instance.follower)
        
        # Takip edilen kişi için rozet kontrolü (followers_count)
        check_and_award_badges(instance.followed)

@receiver(post_delete, sender=Follow)
def follow_deleted_handler(sender, instance, **kwargs):
    # Takip kaldırıldığında da kontrol edelim (rozet kaybı olmaz ama tutarlılık için)
    print(f"Follow deleted: {instance.follower.username} -/-> {instance.followed.username}")
    # Rozet kaybetmeme policy'si varsa burada kontrol edilebilir

# Belki bir şey silindiğinde puan düşürmek de istenebilir
# @receiver(post_delete, sender=Comment)
# def comment_deleted_handler(sender, instance, **kwargs):
#     update_points_and_check_badges(instance.user, -5) 