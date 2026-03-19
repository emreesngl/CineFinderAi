from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView, ListView, TemplateView, View
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache # Cache importu
from .forms import CustomUserCreationForm, CommentForm, RatingForm, UserProfileUpdateForm, MessageForm
from .utils import search_media, get_poster_url, get_popular_media, get_media_details, get_trailer_key, generate_gemini_response, get_tmdb_genres, discover_media_by_genre, get_upcoming_movies, get_now_playing_movies, get_top_rated_media, discover_media, get_tmdb_countries, get_tmdb_watch_providers
from .models import Media, Comment, Rating, UserList, Follow, Message, Notification, ChatConversation, ChatMessage, Badge, UserHiddenConversation
from django.db.models import Avg, Q, Max, OuterRef, Subquery, Case, When, Value, IntegerField
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from django.utils import timezone
import hashlib # Cache anahtarı için hash
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
# API Anahtarı ve Model için import
import ApiKey 
# Markdown işleme için
from django.utils.safestring import mark_safe
import markdown
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string # AJAX için eklendi

User = get_user_model()
CACHE_TIMEOUT_SEARCH = 60 * 15 # 15 dakika cache süresi

# Chatbot sistem talimatı
CHATBOT_SYSTEM_INSTRUCTION = """
Sen bir film ve dizi uzmanısın. Kullanıcılara film ve dizi önerileri verir, film/dizi hakkında detaylı bilgiler paylaşır, 
oyuncu ve yönetmen bilgileri verin. Samimi ve dostça bir ton kullan. Emoji kullanmaktan çekinme. 
Türkçe yanıt ver ve film önerilerinde mümkünse türü, yılını ve kısa açıklamasını da ekle.
"""

# Markdown'ı HTML'e çevirme yardımcı fonksiyonu
def convert_markdown_to_html(value):
    try:
        html = markdown.markdown(value, extensions=['extra', 'nl2br'])
        return mark_safe(html)
    except Exception as md_err:
        print(f"Markdown çevirme hatası: {md_err}")
        from django.template.defaultfilters import linebreaksbr
        return linebreaksbr(value) # Fallback

# Create your views here.

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') # Başarılı kayıt sonrası yönlendirilecek URL (Django'nun varsayılan login URL'si)
    template_name = 'registration/signup.html'

class UserProfileView(DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'profile_user' # Template'de kullanacağımız isim
    slug_field = "username" # URL'den hangi alanla kullanıcıyı bulacağımız
    slug_url_kwarg = "username" # URL'deki parametre adı

    def get_object(self, queryset=None):
        # Eğer URL'de username varsa o kullanıcıyı, yoksa giriş yapmış kullanıcıyı döndür
        username = self.kwargs.get(self.slug_url_kwarg)
        if username:
            return get_object_or_404(User, username=username)
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()

        # Takipçi ve Takip Edilen Sayıları
        context['followers_count'] = profile_user.followers.count()
        context['following_count'] = profile_user.following.count()

        # Giriş yapmış kullanıcının bu profili takip edip etmediği
        context['is_following'] = False
        if self.request.user.is_authenticated and self.request.user != profile_user:
            context['is_following'] = Follow.objects.filter(follower=self.request.user, followed=profile_user).exists()

        # Kullanıcının listelerini al (Optimize edildi: select_related yeterli)
        user_lists = UserList.objects.filter(user=profile_user).select_related('media').order_by('-added_at')
        
        # Poster URL'lerini hesaplamak için fonksiyonu import et
        from .utils import get_poster_url
        
        # Listeleri ayır ve poster URL'lerini ekle
        favorite_list = user_lists.filter(list_type='favorite')
        for item in favorite_list:
            item.computed_poster_url = get_poster_url(item.media.poster_path)
        context['favorite_list'] = favorite_list
        
        watchlist_list = user_lists.filter(list_type='watchlist')
        for item in watchlist_list:
             item.computed_poster_url = get_poster_url(item.media.poster_path)
        context['watchlist_list'] = watchlist_list
        
        follow_list = user_lists.filter(list_type='follow')
        for item in follow_list:
             item.computed_poster_url = get_poster_url(item.media.poster_path)
        context['follow_list'] = follow_list
        
        return context

class SearchView(ListView):
    template_name = 'search_results.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            # Cache anahtarı oluştur
            cache_key = f"search_results_{hashlib.md5(query.encode('utf-8')).hexdigest()}"
            # Cache'i kontrol et
            results = cache.get(cache_key)
            
            if results is None:
                print(f"CACHE MISS: Arama sonuçları getiriliyor - Query: {query}")
                results = search_media(query, media_type='multi') # 'multi' araması devam ediyor
                for result in results:
                    result['poster_url'] = get_poster_url(result.get('poster_path'))
                    if 'media_type' not in result:
                        if result.get('title'): result['media_type'] = 'movie'
                        elif result.get('name'): result['media_type'] = 'tv'
                # Sonuçları cache'le
                cache.set(cache_key, results, CACHE_TIMEOUT_SEARCH)
            else:
                print(f"CACHE HIT: Arama sonuçları cache'den - Query: {query}")
                
            return results
        # Eğer sorgu yoksa, boş liste döndür
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        context['query'] = query
        ai_suggestion = None 
        ai_suggestion_markdown = "" # Ham metin için başlangıç

        if query:
            context['page_title'] = f'Arama Sonuçları: "{query}"'
            print(f"AI önerisi getiriliyor (SearchView - Doğrudan API) - Query: {query}")
            
            # --- Doğrudan Gemini API Çağrısı --- 
            try:
                # Sistem Talimatı (Daha dinamik ve sohbet tarzı)
                search_system_instruction = (
                    f"Selam! Ben Filmbot, senin kişisel sinema rehberin 🎬. '{query}' hakkında konuşalım mı? Harika bir konu! "
                    "İşte sana özel olarak seçtiğim birkaç film/dizi, bakalım ne düşüneceksin:\n"
                    "1. **@@Film/Dizi Adı (Yıl)@@**\n   *Neden mi bu?* Çünkü [buraya içten, arkadaşça ve belki biraz esprili bir yorum/neden ekle. Örneğin: tam kafa dağıtmalık, izlerken kesin duygulanırsın, bu havada battaniye altında süper gider vb.].\n"
                    "2. **@@Başka Film/Dizi Adı (Yıl)@@**\n   *Bunu da listeye aldım!* Sebebi de [farklı, yine samimi bir neden/yorum ekle].\n"
                    "(Mümkünse 5 tane olana kadar aynı formatta devam et)"
                )
                
                # Görev Tanımı (Daha dinamik son)
                task_prompt = (
                    f"Kullanıcı '{query}' ile ilgili arama yaptı. Bu konuyla AKICI ve alakalı 5 film/dizi öner. "
                    "Tonun ÇOK arkadaş canlısı, samimi, esprili ve ENERJİK olsun (gerçek bir sohbet gibi). "
                    "Başlıkları **@@Başlık (Yıl)@@** formatında yaz, altındaki açıklamalar kısa, kişisel ve İÇTEN yorumlar içersin. "
                    "Listeyi sunduktan sonra sabit bir bitiş cümlesi yerine, '{query}' aramasıyla ilgili veya genel olarak sinemayla ilgili arkadaşça, kısa bir kapanış yorumu ekle. Örneğin: 'Umarım beğenirsin!', 'Başka ne tür şeyler seversin?', 'İyi seyirler!' gibi doğal bir ifade kullan."
                 )

                # Final Prompt (History yok, direkt talimat)
                final_prompt = f"{search_system_instruction}\n\n{task_prompt}"

                # Modeli başlat ve mesajı gönder (History yok)
                if not hasattr(ApiKey, 'model'):
                     raise Exception("Hata: ApiKey.py içinde 'model' nesnesi bulunamadı.")
                 
                chat = ApiKey.model.start_chat(history=[])
                response = chat.send_message(final_prompt)

                # Yanıtı işle
                if response.candidates:
                    ai_suggestion_markdown = response.text
                    # Markdown'ı işle (HTML'e çevirirken @@ işaretlerini kaldır veya formatla)
                    processed_markdown = ai_suggestion_markdown.replace('@@', '**') # @@ yerine ** kullanabiliriz
                    ai_suggestion = convert_markdown_to_html(processed_markdown)
                else:
                    print("Gemini Yanıtı Engellendi/Boş (SearchView):", response.prompt_feedback)
                    ai_suggestion = "AI önerisi alınırken bir sorun oluştu (Engellendi/Boş)."
                    ai_suggestion_markdown = ""
                    
            except Exception as e:
                print(f"Doğrudan AI önerisi alınırken hata (SearchView): {e}")
                ai_suggestion = "AI önerisi alınırken bir sorun oluştu." 
                ai_suggestion_markdown = ""

            context['ai_suggestion'] = ai_suggestion # İşlenmiş HTML
            context['ai_suggestion_raw'] = ai_suggestion_markdown # Ham metni sakla
                 
        else:
            context['page_title'] = "Film ve Dizi Ara"
            context['ai_suggestion'] = None
            context['ai_suggestion_raw'] = ""

        return context

class PopularMediaView(ListView):
    template_name = 'catalog.html'
    context_object_name = 'media_list'
    paginate_by = 20 # TMDB genellikle sayfa başına 20 sonuç döner
    cache_timeout_short = 60 * 15 # 15 dakika
    cache_timeout_long = 60 * 60 * 24 # 1 gün
    cache_timeout_catalog_search = 60 * 10 # Katalog araması için 10 dakika cache

    def get_queryset(self):
        # API veya arama kullandığımız için None döndürüyoruz
        return None

    def get_context_data(self, **kwargs):
        context = {} # Context\'i manuel oluştur
        request = self.request
        query = request.GET.get('q') # Arama sorgusunu al
        media_type = request.GET.get('type', 'movie')
        if media_type not in ['movie', 'tv']:
            media_type = 'movie'
        
        context['media_type'] = media_type # Medya tipini context\'e ekle

        # ARAMA VARSA:
        if query:
            context['page_title'] = f'Katalog Arama: "{query}"'
            context['is_search'] = True # Template\'te filtreleri gizlemek vb. için flag
            
            # Arama sonuçları için cache anahtarı
            search_cache_key = f"catalog_search_{media_type}_{hashlib.md5(query.encode('utf-8')).hexdigest()}"
            results_data = cache.get(search_cache_key)
            
            if results_data is None:
                print(f"CACHE MISS: Katalog araması getiriliyor - Type: {media_type}, Query: {query}")
                # Sadece film veya dizi içinde ara, multi değil
                search_results = search_media(query, media_type=media_type) 
                results_data = {'results': search_results}
                cache.set(search_cache_key, results_data, self.cache_timeout_catalog_search)
            else:
                print(f"CACHE HIT: Katalog araması cache\'den - Type: {media_type}, Query: {query}")

            media_list_raw = results_data.get('results', [])
            total_results = len(media_list_raw) # Arama API\'si sayfalama yapmıyor
            total_pages = 1

            # Poster URL\'lerini ekle
            for result in media_list_raw:
                result['poster_url'] = get_poster_url(result.get('poster_path'))
                result['media_type'] = media_type # Arama tipine göre media_type ekle

            # Arama için sayfalama uygulamayalım (TMDB search tek sayfa döner)
            paginator = Paginator(media_list_raw, len(media_list_raw) if media_list_raw else 1) # Tek sayfa
            page_obj = paginator.page(1)
            context['media_list'] = media_list_raw
            context['page_obj'] = page_obj
            context['is_paginated'] = False
            # Filtreleri boş gönderelim
            context['genres'] = []
            context['countries'] = []
            context['selected_genres'] = []
            context['selected_country'] = None
            context['list_type'] = 'all'
            context['selected_sort'] = 'relevance' # Arama için varsayılan
            context['year_gte'] = None
            context['year_lte'] = None
            context['vote_average_gte'] = None
            context['vote_average_lte'] = None
            context['url_params'] = f"q={query}&type={media_type}" # Sayfalama linkleri için (gerçi sayfalama yok)
            
            return context
        
        # ARAMA YOKSA (Normal Katalog Gösterimi):
        else:
            context['is_search'] = False # Arama olmadığını belirt
            # Filtre parametrelerini al ve temizle/doğrula
            page = int(request.GET.get('page', 1))
            sort_by = request.GET.get('sort_by', 'popularity.desc')
            selected_genres = request.GET.getlist('genre')
            selected_genres = sorted([g for g in selected_genres if g]) # Sıralı tutalım
            list_type = request.GET.get('list_type', 'all')
            
            # Yeni filtre parametreleri
            release_date_gte = request.GET.get('release_date.gte')
            release_date_lte = request.GET.get('release_date.lte')
            with_watch_providers = request.GET.get('with_watch_providers')
            with_keywords = request.GET.get('with_keywords')
            with_original_language = request.GET.get('with_original_language')
            show_me = request.GET.get('show_me', 'everything')
            include_adult = request.GET.get('include_adult')
            search_all_releases = request.GET.get('search_all_releases')
            
            # Eski parametreler (geriye uyumluluk için)
            year_gte = request.GET.get('year_gte')
            year_lte = request.GET.get('year_lte')
            vote_gte = request.GET.get('vote_average_gte')
            vote_lte = request.GET.get('vote_average_lte')
            vote_count_gte = request.GET.get('vote_count_gte')
            runtime_gte = request.GET.get('runtime_gte')
            runtime_lte = request.GET.get('runtime_lte')
            with_status = request.GET.get('with_status')
            with_networks = request.GET.get('with_networks')
            selected_country = request.GET.get('country')
    
            # API parametrelerini oluştur (cache anahtarı için de kullanılacak)
            api_params = {
                'page': page,
                'sort_by': sort_by,
                **({'with_genres': selected_genres} if selected_genres else {}),
                **({'release_date.gte': release_date_gte} if release_date_gte else {}),
                **({'release_date.lte': release_date_lte} if release_date_lte else {}),
                **({'with_watch_providers': with_watch_providers} if with_watch_providers else {}),
                **({'with_keywords': with_keywords} if with_keywords else {}),
                **({'with_original_language': with_original_language} if with_original_language else {}),
                **({'include_adult': include_adult} if include_adult else {}),
                # Eski parametreler (geriye uyumluluk)
                **({'year_gte': year_gte} if year_gte else {}),
                **({'year_lte': year_lte} if year_lte else {}),
                **({'vote_average.gte': vote_gte} if vote_gte else {}),
                **({'vote_average.lte': vote_lte} if vote_lte else {}),
                **({'vote_count.gte': vote_count_gte} if vote_count_gte else {}),
                **({'runtime.gte': runtime_gte} if runtime_gte and media_type == 'movie' else {}),
                **({'runtime.lte': runtime_lte} if runtime_lte and media_type == 'movie' else {}),
                **({'with_status': with_status} if with_status and media_type == 'tv' else {}),
                **({'with_networks': with_networks} if with_networks and media_type == 'tv' else {}),
                **({'with_origin_country': selected_country} if selected_country else {})
            }
    
            # --- Cache Anahtarları --- 
            genres_cache_key = f'tmdb_genres_{media_type}'
            countries_cache_key = 'tmdb_countries'
            providers_cache_key = f'tmdb_providers_{media_type}'
            params_str = f"{media_type}_{list_type}_" + json.dumps(api_params, sort_keys=True)
            media_list_cache_key = f'tmdb_list_{hashlib.md5(params_str.encode("utf-8")).hexdigest()}'
            
            # --- Türleri Cache'den Al veya Getir --- 
            all_genres = cache.get(genres_cache_key)
            if not all_genres:
                print(f"CACHE MISS: Türler getiriliyor ({media_type})")
                all_genres = get_tmdb_genres(media_type)
                cache.set(genres_cache_key, all_genres, self.cache_timeout_long)
            else:
                print(f"CACHE HIT: Türler cache'den ({media_type})")
            
            # --- Ülkeleri Cache'den Al veya Getir --- 
            all_countries = cache.get(countries_cache_key)
            if not all_countries:
                print("CACHE MISS: Ülkeler getiriliyor")
                all_countries = get_tmdb_countries()
                cache.set(countries_cache_key, all_countries, self.cache_timeout_long)
            else:
                print("CACHE HIT: Ülkeler cache'den")

            # --- Platformları Cache'den Al veya Getir --- 
            all_providers = cache.get(providers_cache_key)
            if not all_providers:
                print(f"CACHE MISS: Platformlar getiriliyor ({media_type})")
                all_providers = get_tmdb_watch_providers(media_type, 'TR')
                cache.set(providers_cache_key, all_providers, self.cache_timeout_long)
            else:
                print(f"CACHE HIT: Platformlar cache'den ({media_type})")
    
            # --- Medya Listesini Cache'den Al veya Getir ---
            results_data = cache.get(media_list_cache_key)
            if not results_data:
                print(f"CACHE MISS: Medya listesi getiriliyor - Key: {media_list_cache_key}")
                use_discover = True
                title_prefix = ""
                
                # Özel liste türleri
                if list_type == 'popular':
                     api_params['sort_by'] = 'popularity.desc'
                     title_prefix = "Popüler"
                elif list_type == 'top_rated':
                     api_params['sort_by'] = 'vote_average.desc'
                     title_prefix = "En İyi"
                elif list_type == 'upcoming' and media_type == 'movie':
                    results = get_upcoming_movies(page=page)
                    # TMDB /movie/upcoming sayfası toplam sayfa/sonuç döndürmüyor, manuel ekleyelim
                    results_data = {'results': results, 'total_pages': 20, 'total_results': 400} # Tahmini değerler
                    use_discover = False
                    title_prefix = "Yakında Çıkacak"
                elif list_type == 'now_playing' and media_type == 'movie':
                    results = get_now_playing_movies(page=page)
                    # TMDB /movie/now_playing sayfası toplam sayfa/sonuç döndürmüyor, manuel ekleyelim
                    results_data = {'results': results, 'total_pages': 50, 'total_results': 1000} # Tahmini değerler
                    use_discover = False
                    title_prefix = "Gösterimdeki"
                    
                if use_discover:
                    results_data = discover_media(media_type, api_params)
                    # API'den gelen başlık için özel liste türlerini kontrol et
                    if list_type == 'popular': title_prefix = "Popüler"
                    elif list_type == 'top_rated': title_prefix = "En İyi"
                    
                # Sonucu cache'le
                cache.set(media_list_cache_key, results_data, self.cache_timeout_short)
                # Başlığı da cache'le
                cache.set(media_list_cache_key + '_title', title_prefix, self.cache_timeout_short)
            else:
                 print(f"CACHE HIT: Medya listesi cache'den - Key: {media_list_cache_key}")
                 title_prefix = cache.get(media_list_cache_key + '_title', "") # Cache'den başlığı al
            
            media_list_raw = results_data.get('results', [])
            
            # "Görmediğim filmler/diziler" filtresi
            if show_me == 'not_seen' and request.user.is_authenticated:
                print(f"DEBUG: Görmediğim {media_type} filtresi uygulanıyor")
                # Kullanıcının etkileşime girdiği medya ID'lerini al
                user_interacted_tmdb_ids = set(
                    UserList.objects.filter(user=request.user)
                    .values_list('media__tmdb_id', flat=True)
                )
                print(f"DEBUG: Kullanıcının etkileşime girdiği medya sayısı: {len(user_interacted_tmdb_ids)}")
                # Etkileşime girmediği medyaları filtrele
                original_count = len(media_list_raw)
                media_list_raw = [
                    media for media in media_list_raw 
                    if str(media.get('id')) not in user_interacted_tmdb_ids
                ]
                print(f"DEBUG: Filtreleme sonrası: {len(media_list_raw)}/{original_count}")
            elif show_me == 'seen' and request.user.is_authenticated:
                print(f"DEBUG: Gördüğüm {media_type} filtresi uygulanıyor")
                # Kullanıcının etkileşime girdiği medya ID'lerini al
                user_interacted_tmdb_ids = set(
                    UserList.objects.filter(user=request.user)
                    .values_list('media__tmdb_id', flat=True)
                )
                # Etkileşime girdiği medyaları filtrele
                original_count = len(media_list_raw)
                media_list_raw = [
                    media for media in media_list_raw 
                    if str(media.get('id')) in user_interacted_tmdb_ids
                ]
                print(f"DEBUG: Filtreleme sonrası: {len(media_list_raw)}/{original_count}")
            else:
                print(f"DEBUG: show_me parametresi: {show_me}, authenticated: {request.user.is_authenticated}")
            
            total_results = len(media_list_raw) if show_me != 'everything' else results_data.get('total_results', 0)
            # TMDB max 500 sayfa döndürüyor
            total_pages = min(results_data.get('total_pages', 1), 500) if total_results > 0 else 1
    
            # Poster URL\'lerini ve eksik media_type\'ları ekle
            for result in media_list_raw:
                result['poster_url'] = get_poster_url(result.get('poster_path'))
                if 'media_type' not in result or not result['media_type']:
                    result['media_type'] = media_type
                    
            # Manuel Paginator
            object_list_for_paginator = range(total_results) if total_results > 0 else []
            paginator = Paginator(object_list_for_paginator, self.paginate_by)
            paginator.num_pages = total_pages 
            
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page = 1
                page_obj = paginator.page(page)
            except EmptyPage:
                page = paginator.num_pages
                page_obj = paginator.page(page)
            
            # --- Context Oluşturma --- 
            context['paginator'] = paginator
            context['page_obj'] = page_obj
            context['is_paginated'] = page_obj.has_other_pages()
            context['media_list'] = media_list_raw 
    
            # Filtreleme için context verileri
            context['genres'] = all_genres
            context['countries'] = all_countries
            context['providers'] = all_providers
            context['selected_genres'] = selected_genres
            context['selected_country'] = selected_country
            context['list_type'] = list_type
            context['selected_sort'] = sort_by
            
            # Yeni filtre değerleri
            context['release_date_gte'] = release_date_gte
            context['release_date_lte'] = release_date_lte
            context['with_watch_providers'] = with_watch_providers
            context['with_keywords'] = with_keywords
            context['with_original_language'] = with_original_language
            context['show_me'] = show_me
            context['include_adult'] = include_adult
            context['search_all_releases'] = search_all_releases
            
            # Platform seçimlerini işle
            selected_providers = []
            if with_watch_providers:
                selected_providers = with_watch_providers.split('|')
            context['selected_providers'] = selected_providers
            
            # Eski filtre değerleri (geriye uyumluluk)
            context['year_gte'] = year_gte
            context['year_lte'] = year_lte
            context['vote_average_gte'] = vote_gte
            context['vote_average_lte'] = vote_lte
            context['vote_count_gte'] = vote_count_gte
            context['runtime_gte'] = runtime_gte
            context['runtime_lte'] = runtime_lte
            context['with_status'] = with_status
            context['with_networks'] = with_networks
            
            # Dinamik Başlık
            title_parts = []
            if title_prefix:
                title_parts.append(title_prefix)
                
            if media_type == 'movie':
                title_parts.append("Filmler")
            else:
                title_parts.append("Diziler")
                
            context['page_title'] = " ".join(title_parts)
            
            # URL parametrelerini template\'e gönder (sayfalama ve filtreler için)
            url_params = request.GET.copy()
            if 'page' in url_params:
                del url_params['page']
            context['url_params'] = url_params.urlencode()
            
        return context

class MediaDetailView(DetailView):
    template_name = 'new_media_detail.html'
    # Model'i doğrudan belirtmiyoruz çünkü hem API'den veri çekiyoruz hem de DB'den
    context_object_name = 'media_details'

    def get_object(self, queryset=None):
        # URL'den parametreleri al
        media_type = self.kwargs.get('media_type')
        media_id = self.kwargs.get('media_id')

        if not media_type or not media_id:
            raise Http404("Medya türü veya ID belirtilmedi.")

        # Veritabanında medya var mı kontrol et, yoksa oluştur
        media, created = Media.objects.get_or_create(
            tmdb_id=media_id,
            media_type=media_type,
            defaults={'title': 'Başlık Bekleniyor...'} # Geçici başlık
        )

        # TMDB'den medya detaylarını çek (credits, videos, similar, images dahil)
        media_details = get_media_details(media_id, media_type)
        if not media_details:
            raise Http404("Medya detayları bulunamadı.")

        # Veritabanındaki başlığı ve poster path'i güncelle (eğer boşsa veya farklıysa)
        api_title = media_details.get('title') if media_type == 'movie' else media_details.get('name')
        api_poster_path = media_details.get('poster_path') # poster_path'i al
        
        needs_save = False
        if api_title and (created or media.title != api_title):
            media.title = api_title
            needs_save = True
        if api_poster_path and media.poster_path != api_poster_path:
            media.poster_path = api_poster_path
            needs_save = True
            
        if needs_save:
            media.save()
        
        media_details['db_object'] = media # DB nesnesini context'e ekle

        # Puan ortalamasını ve kullanıcı puanını hesapla/getir
        media_details['vote_average'] = Rating.objects.filter(media=media).aggregate(Avg('score'))['score__avg'] or 0.0
        media_details['vote_count'] = Rating.objects.filter(media=media).count()
        
        # Poster URL'ini context'e ekle (veritabanındaki path'ten)
        media_details['poster_url'] = get_poster_url(media.poster_path)
        
        # Benzer filmleri/dizileri context için işle
        similar_media_raw = media_details.get('similar', {}).get('results', [])
        processed_similar_media = []
        for item in similar_media_raw:
            item['poster_url'] = get_poster_url(item.get('poster_path'))
            # Gelen her item için media_type ekleyelim
            item['media_type'] = item.get('media_type', media_type)
            processed_similar_media.append(item)
        media_details['similar_media'] = processed_similar_media
            
        # Fragman key'ini al (videolar kısmından)
        media_details['trailer_key'] = None
        videos = media_details.get('videos', {}).get('results', [])
        for video in videos:
             if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                media_details['trailer_key'] = video['key']
                break # İlk bulunan fragmanı al

        return media_details

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media = context['media_details']['db_object']
        user = self.request.user

        # Yorumları getir ve formu ekle
        context['comments'] = Comment.objects.filter(media=media).select_related('user').order_by('-created_at')
        context['comment_form'] = CommentForm()

        # Kullanıcı giriş yapmışsa listelerini ve puanını kontrol et
        context['user_rating'] = None
        context['is_in_favorite'] = False
        context['is_in_watchlist'] = False
        context['is_in_follow'] = False
        if user.is_authenticated:
            # Puan
            rating = Rating.objects.filter(user=user, media=media).first()
            context['user_rating'] = rating.score if rating else None
            # Listeler
            user_lists = UserList.objects.filter(user=user, media=media).values_list('list_type', flat=True)
            context['is_in_favorite'] = 'favorite' in user_lists
            context['is_in_watchlist'] = 'watchlist' in user_lists
            context['is_in_follow'] = 'follow' in user_lists

        # Puanlama için 1-10 arası sayılar
        context['rating_range'] = range(1, 11)

        return context

class UpdateUserListView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        media_id = request.POST.get('media_id')
        list_type = request.POST.get('list_type')
        action = request.POST.get('action')
        user = request.user
        
        # Doğrulama
        if not media_id or not list_type or not action:
            messages.error(request, "Eksik veya geçersiz parametre.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        try:
            media = Media.objects.get(id=media_id)
        except Media.DoesNotExist:
            messages.error(request, "Medya bulunamadı.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        if list_type not in [choice[0] for choice in UserList.LIST_TYPE_CHOICES]:
            messages.error(request, "Geçersiz liste türü.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if action == 'add':
            # Eğer aynı türden liste varsa oluşturma, hata ver
            if UserList.objects.filter(user=user, media=media, list_type=list_type).exists():
                messages.warning(request, f"{media.title or 'Medya'}, zaten '{dict(UserList.LIST_TYPE_CHOICES)[list_type]}' listenizde.")
            else:
                UserList.objects.create(user=user, media=media, list_type=list_type)
                messages.success(request, f"{media.title or 'Medya'}, '{dict(UserList.LIST_TYPE_CHOICES)[list_type]}' listesine eklendi.")
        elif action == 'remove':
            deleted, _ = UserList.objects.filter(user=user, media=media, list_type=list_type).delete()
            if deleted:
                messages.success(request, f"{media.title or 'Medya'}, '{dict(UserList.LIST_TYPE_CHOICES)[list_type]}' listesinden kaldırıldı.")
            else:
                messages.warning(request, f"{media.title or 'Medya'}, zaten '{dict(UserList.LIST_TYPE_CHOICES)[list_type]}' listenizde değil.")
        else:
            messages.error(request, "Geçersiz işlem türü.")

        # Kullanıcıyı geldiği sayfaya geri yönlendir
        return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@require_POST
def add_comment_view(request, media_id):
    try:
        media = Media.objects.get(id=media_id)
    except Media.DoesNotExist:
        # AJAX isteği için JSON hatası döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Medya bulunamadı.'}, status=404)
        raise Http404("Medya bulunamadı.")

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.media = media
        comment.save()
        
        # AJAX isteği için JSON yanıtı döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'username': request.user.username,
                'created_at': comment.created_at.strftime("%d %b %Y %H:%M") # Formatı template ile aynı yap
            })
        
        messages.success(request, "Yorumunuz başarıyla eklendi.")
        # Sayfayı yenilemek yerine geldiği yere yönlendir
        return redirect(request.META.get('HTTP_REFERER', reverse('media_detail', args=[media.media_type, media.tmdb_id])))
    else:
        # AJAX isteği için JSON hatası döndür
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Form hatalarını JSON olarak döndürmek daha detaylı olabilir, şimdilik genel hata
            return JsonResponse({'success': False, 'error': 'Yorum içeriği geçersiz.'}, status=400)
            
        # Normal istek için hata mesajı göster
        messages.error(request, "Yorum eklenirken bir hata oluştu. Lütfen tekrar deneyin.")
        return redirect(request.META.get('HTTP_REFERER', reverse('media_detail', args=[media.media_type, media.tmdb_id])))

class RateMediaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        media_id = request.POST.get('media_id')
        score = request.POST.get('score')
        user = request.user

        # Doğrulama
        if not media_id or not score:
            messages.error(request, "Eksik parametre: Medya ID veya Puan.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            media = Media.objects.get(id=media_id)
            score = int(score)
            if not (1 <= score <= 10):
                 raise ValueError("Puan 1-10 arasında olmalı.")
        except Media.DoesNotExist:
            messages.error(request, "Medya bulunamadı.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        except (ValueError, TypeError):
            messages.error(request, "Geçersiz puan değeri.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Kullanıcının bu medya için önceki puanını al (varsa)
        previous_rating = Rating.objects.filter(user=user, media=media).first()
        is_first_rating_for_this_media = previous_rating is None

        # Mevcut puanı güncelle veya yeni puan oluştur
        rating, created = Rating.objects.update_or_create(
            user=user,
            media=media,
            defaults={'score': score}
        )

        # --- Puan ve Seviye Mantığı (Signals rozet kontrolünü yapacak) ---
        user_updated = False
        
        # Sadece bu medya için ilk kez puan veriyorsa puan ekle
        if is_first_rating_for_this_media:
            user.points += 5
            user_updated = True

        # Seviyeyi güncelle
        new_level = (user.points // 50) + 1
        level_up_message = ""
        if new_level > user.level:
            level_up_message = f" 🎉 Seviye atladınız! Yeni seviyeniz: {new_level}."
            user.level = new_level
            user_updated = True

        # Kullanıcı modelini sadece gerekliyse kaydet (signals otomatik rozet kontrolü yapacak)
        if user_updated:
            user.save()

        # Başarı mesajını oluştur
        if created:
            message_text = f"⭐ {media.title or 'Medya'} için {score}/10 puan verdiniz."
        else:
            message_text = f"🔄 {media.title or 'Medya'} için puanınızı {score}/10 olarak güncellediniz."

        # Seviye atlama mesajını ekle
        full_message = message_text + level_up_message
        messages.success(request, full_message)

        return redirect(request.META.get('HTTP_REFERER', '/'))

# --- Notifications View ---
class NotificationsView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        # Mesaj bildirimleri hariç, sadece takip ve diğer sistem bildirimlerini getir
        queryset = Notification.objects.filter(
            user=self.request.user
        ).exclude(
            message__contains='mesaj gönderdi'  # Mesaj bildirimlerini hariç tut
        ).exclude(
            message__contains='size mesaj'  # Mesaj bildirimlerini hariç tut
        ).exclude(
            message__contains='yeni mesaj'  # Mesaj bildirimlerini hariç tut
        ).order_by('-created_at')
        
        Notification.objects.filter(user=self.request.user, is_read=False).update(is_read=True)
        
        processed_notifications = []
        from django.templatetags.static import static
        default_avatar_url = static('images/default_avatar.png')
        # print(f"[DEBUG] Default Avatar URL: {default_avatar_url}") # Log kaldırıldı
        
        for notification in queryset:
            sender_username = None
            cleaned_message = notification.message
            sender_profile_pic_url = default_avatar_url
            # log_prefix = f"[DEBUG] Notification ID {notification.id}:" # Log kaldırıldı
            
            if "::" in notification.message:
                parts = notification.message.split("::", 1)
                sender_username = parts[0]
                cleaned_message = parts[1]
                
                # print(f"{log_prefix} Sender username extracted: {sender_username}") # Log kaldırıldı
                try:
                    sender = User.objects.get(username=sender_username)
                    # print(f"{log_prefix} Sender object found: {sender}") # Log kaldırıldı
                    if sender.profile_picture:
                        try:
                             pic_url = sender.profile_picture.url
                             sender_profile_pic_url = pic_url
                             # print(f"{log_prefix} Found profile picture URL: {sender_profile_pic_url}") # Log kaldırıldı
                        except Exception as e:
                             print(f"Bildirim ({notification.id}) profil resmi URL alınırken hata: {e}")
                             # sender_profile_pic_url varsayılan olarak kalır
                    # else:
                        # print(f"{log_prefix} Sender has no profile picture, using default.") # Log kaldırıldı
                         
                except User.DoesNotExist:
                    sender_username = "Bilinmeyen Kullanıcı"
                    # print(f"{log_prefix} Sender DoesNotExist, using default avatar.") # Log kaldırıldı
                    pass 
            else:
                 sender_username = "Sistem" 
                 # print(f"{log_prefix} No sender prefix found, assuming 'Sistem', using default avatar.") # Log kaldırıldı
            
            processed_notifications.append({
                'id': notification.id,
                'message': cleaned_message, 
                'link': notification.link,
                'created_at': notification.created_at,
                'sender_username': sender_username,
                'sender_profile_pic_url': sender_profile_pic_url
            })
            # print(f"{log_prefix} Final assigned URL: {sender_profile_pic_url}") # Log kaldırıldı
            
        return processed_notifications

    # Pagination şablonunda hata olmaması için context'e media_type ekleyelim
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['media_type'] = None # veya ''
        return context

# --------------------------

class ChatbotView(View):
    template_name = 'chatbot.html'

    def get(self, request, *args, **kwargs):
        context = {}
        if request.user.is_authenticated:
        # Kullanıcının geçmiş konuşmalarını al
            conversations = ChatConversation.objects.filter(user=request.user).order_by('-updated_at')
            context['conversations'] = conversations
            context['needs_login'] = False
        else:
            # Giriş yapmamış kullanıcı için boş liste ve işaretçi
            context['conversations'] = []
            context['needs_login'] = True
            
        return render(request, self.template_name, context)

class ChatSendMessageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message_text = data.get('message')
            conversation_id = data.get('conversation_id') # Frontend'den gelen ID

            if not message_text:
                return JsonResponse({'error': 'Mesaj boş olamaz.'}, status=400)

            user = request.user
            conversation = None
            is_new_conversation = False

            # Mevcut konuşmayı bul veya yeni oluştur
            if conversation_id:
                try:
                    # Mevcut konuşmayı ID ile bul
                    conversation = ChatConversation.objects.get(id=conversation_id, user=user)
                except ChatConversation.DoesNotExist:
                    return JsonResponse({'error': 'Konuşma bulunamadı veya size ait değil.'}, status=404)
            else:
                # Yeni konuşma oluştur
                # İlk mesajın bir kısmını başlık yapalım (isteğe bağlı)
                conversation_title = message_text[:50] + "..." if len(message_text) > 50 else message_text
                conversation = ChatConversation.objects.create(user=user, title=conversation_title)
                is_new_conversation = True

            # Kullanıcı mesajını kaydet
            message = ChatMessage.objects.create(
                conversation=conversation,
                sender_is_user=True,
                text=message_text
            )

            # --- Konuşma Geçmişini Al --- 
            history_messages = ChatMessage.objects.filter(conversation=conversation).order_by('-sent_at')[:5] # Son 5 mesajı al (ayarlanabilir)
            history = []
            for msg in reversed(history_messages): # Gemini için kronolojik sıra (eskiden yeniye)
                role = "user" if msg.sender_is_user else "model"
                history.append({"role": role, "parts": [{"text": msg.text}]})
            # Mevcut kullanıcı mesajını da ekle (eğer history'de yoksa)
            if not history or history[-1]['parts'][0]['text'] != message_text:
                 history.append({"role": "user", "parts": [{"text": message_text}]})
            # -----------------------------

            # Gemini API'ye gönder (artık geçmişle birlikte)
            ai_response_dict = generate_gemini_response(message_text, history=history) # Sözlük döndürecek
            ai_text = ai_response_dict.get('text', 'Üzgünüm, bir yanıt alamadım.')

            # AI yanıtını kaydet (öneri verisiyle birlikte)
            ChatMessage.objects.create(
                conversation=conversation,
                sender_is_user=False,
                text=ai_text
            )

            # Konuşmanın son güncellenme zamanını güncelle
            conversation.save()
            
            # --- İlk Mesaj Kontrolü Başlangıcı ---
            is_first_message = ChatMessage.objects.filter(
                (Q(sender_is_user=True) & Q(conversation=conversation))
            ).count() == 1
            # --- İlk Mesaj Kontrolü Sonu ---
            
            # Frontend'e gönderilecek JSON yanıtı
            response_data = {
                'reply': ai_text,
                'conversation_id': conversation.id,
                'is_new_conversation': is_new_conversation,
                'conversation_title': conversation.title
            }
            
            # Eğer ilk mesaj ise, yanıtı yönlendirme URL'si ile güncelle
            if is_first_message:
                response_data['redirect_url'] = reverse('inbox')
                print(f"İlk mesaj gönderildi. Yönlendirme URL'si eklendi: {response_data['redirect_url']}")

            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Geçersiz JSON formatı.'}, status=400)
        except Exception as e:
            print(f"Chatbot Hata: {e}") 
            return JsonResponse({'error': 'Mesaj işlenirken bir hata oluştu.'}, status=500)

class StreamingChatView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message_text = data.get('message')
            conversation_id = data.get('conversation_id')

            if not message_text:
                return JsonResponse({'error': 'Mesaj boş olamaz.'}, status=400)

            user = request.user
            conversation = None

            # Mevcut konuşmayı bul veya yeni oluştur
            if conversation_id:
                try:
                    conversation = ChatConversation.objects.get(id=conversation_id, user=user)
                except ChatConversation.DoesNotExist:
                    return JsonResponse({'error': 'Konuşma bulunamadı.'}, status=404)
            else:
                # Yeni konuşma oluştur
                conversation_title = message_text[:50] + "..." if len(message_text) > 50 else message_text
                conversation = ChatConversation.objects.create(user=user, title=conversation_title)

            # Kullanıcı mesajını kaydet
            user_message = ChatMessage.objects.create(
                conversation=conversation,
                sender_is_user=True,
                text=message_text
            )

            # Streaming response döndür
            def generate_stream():
                try:
                    # Konuşma geçmişini al
                    history_messages = ChatMessage.objects.filter(conversation=conversation).order_by('-sent_at')[:5]
                    history = []
                    for msg in reversed(history_messages):
                        role = "user" if msg.sender_is_user else "model"
                        history.append({"role": role, "parts": [{"text": msg.text}]})

                    # Stream başlatma mesajı
                    yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation.id, 'is_new': not conversation_id})}\n\n"

                    # Gemini API ile streaming
                    if not hasattr(ApiKey, 'model'):
                        yield f"data: {json.dumps({'type': 'error', 'message': 'AI modeli bulunamadı.'})}\n\n"
                        return

                    chat = ApiKey.model.start_chat(history=history[:-1] if history else [])
                    
                    # Sistem talimatı ile birlikte mesajı gönder
                    full_prompt = f"{CHATBOT_SYSTEM_INSTRUCTION}\n\nKullanıcı: {message_text}"
                    
                    response_stream = chat.send_message(full_prompt, stream=True)
                    
                    full_response = ""
                    for chunk in response_stream:
                        if chunk.text:
                            chunk_text = chunk.text
                            full_response += chunk_text
                            # Her chunk'ı gönder
                            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk_text})}\n\n"
                    
                    # AI mesajını veritabanına kaydet
                    ChatMessage.objects.create(
                        conversation=conversation,
                        sender_is_user=False,
                        text=full_response
                    )
                    
                    # Konuşmanın son güncellenme zamanını güncelle
                    conversation.save()
                    
                    # Stream bitişi
                    yield f"data: {json.dumps({'type': 'end', 'conversation_title': conversation.title})}\n\n"

                except Exception as e:
                    print(f"Streaming hatası: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Bir hata oluştu: {str(e)}'})}\n\n"

            response = StreamingHttpResponse(generate_stream(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Geçersiz JSON formatı.'}, status=400)
        except Exception as e:
            print(f"Streaming Chat Hata: {e}")
            return JsonResponse({'error': 'Mesaj işlenirken bir hata oluştu.'}, status=500)

class ToggleFollowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_id_to_toggle = request.POST.get('user_id')
        if not user_id_to_toggle:
            return JsonResponse({'status': 'error', 'message': 'Kullanıcı ID eksik.'}, status=400)

        try:
            user_to_follow = User.objects.get(id=user_id_to_toggle)
        except User.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'}, status=404)
        except ValueError:
             return JsonResponse({'status': 'error', 'message': 'Geçersiz Kullanıcı ID.'}, status=400)

        # Kendini takip etmeyi engelle
        if request.user == user_to_follow:
             return JsonResponse({'status': 'error', 'message': 'Kendinizi takip edemezsiniz.'}, status=400)

        # Takip durumunu değiştir
        follow_instance, created = Follow.objects.get_or_create(
            follower=request.user,
            followed=user_to_follow
        )

        is_following = False
        if not created:
            follow_instance.delete()
            message = f'{user_to_follow.username} takipten çıkarıldı.'
            is_following = False
            # Takipten çıkınca ilgili bildirimleri silmeyelim, kafa karıştırabilir.
        else:
            message = f'{user_to_follow.username} takip edildi.'
            is_following = True
            
            # Takip edildiğinde bildirim oluşturmadan önce eskileri temizle
            try:
                # Bu kullanıcıdan gelen ÖNCEKİ TÜM (okunmuş/okunmamış) takip/mesaj bildirimlerini silelim mi? 
                # Veya SADECE OKUNMAMIŞ olanları mı? Şimdilik okunmamış olanları silelim.
                # Takip etme/çıkarma için link profile gider
                profile_link = reverse('user_profile', kwargs={'username': request.user.username})
                Notification.objects.filter(
                    user=user_to_follow, # Bildirimi alan (takip edilen)
                    message__startswith=f"{request.user.username}::", # Gönderen bu kullanıcı
                    link=profile_link, # Link takip linki olacak
                    is_read=False # Sadece okunmamışları sil
                ).delete()
                
                # Yeni bildirimi oluştur
                Notification.objects.create(
                    user=user_to_follow, 
                    message=f"{request.user.username}::sizi takip etmeye başladı.",
                    link=profile_link 
                )
            except Exception as e:
                print(f"Takip bildirimi oluşturulurken/silinirken hata: {e}")

        # Güncel takipçi sayısını al
        follower_count = user_to_follow.followers.count()

        return JsonResponse({
            'status': 'success',
            'message': message, 
            'is_following': is_following,
            'follower_count': follower_count
        })

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileUpdateForm
    template_name = 'profile_edit.html'
    success_url = reverse_lazy('profile') # Başarılı güncelleme sonrası kullanıcının profil sayfasına dönsün

    def get_object(self, queryset=None):
        # Sadece giriş yapmış kullanıcının kendi nesnesini döndür
        return self.request.user

    def get_success_url(self):
        # Başarılı güncelleme sonrası kullanıcının kendi profil sayfasına yönlendir
        return reverse('profile') # 'user_profile' yerine 'profile' olmalı

    def form_valid(self, form):
        messages.success(self.request, "Profiliniz başarıyla güncellendi.")
        return super().form_valid(form)

class InboxView(LoginRequiredMixin, ListView):
    template_name = 'inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        user = self.request.user

        # Kullanıcının gizlediği diğer kullanıcıların ID'lerini al
        hidden_user_ids = UserHiddenConversation.objects.filter(user=user).values_list('other_user_id', flat=True)
        
        # Mesajlaşma olan diğer kullanıcıları al, ancak gizlenenleri çıkar
        other_users = User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).exclude(id__in=hidden_user_ids).distinct() # Gizlenenleri exclude et
        
        latest_message_subquery = Message.objects.filter(
            (Q(sender=OuterRef('id'), receiver=user) | Q(sender=user, receiver=OuterRef('id')))
        ).order_by('-sent_at').values('sent_at')[:1]
        
        conversations = other_users.annotate(
            last_message_time=Subquery(latest_message_subquery)
        ).order_by('-last_message_time')
        
        conversation_data = []
        for other_user in conversations:
            try:
                last_message = Message.objects.filter(
                 (Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user))
                ).latest('sent_at')
            except Message.DoesNotExist:
                last_message = None
            
            unread_count = Message.objects.filter(
                sender=other_user,
                receiver=user,
                is_read=False
            ).count()
            
            profile_pic_url = None
            if other_user.profile_picture:
                profile_pic_url = other_user.profile_picture.url
            else:
                from django.templatetags.static import static
                profile_pic_url = static('images/default_avatar.png')
            
            conversation_data.append({
                'user': other_user,
                'profile_pic_url': profile_pic_url,
                'last_message': last_message,
                'unread_count': unread_count,
            })
            
        return conversation_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Sohbetler"
        return context

class ConversationView(LoginRequiredMixin, View):
    template_name = 'conversation.html'
    partial_template_name = 'includes/_conversation_content.html'

    def get(self, request, username):
        # select_related('profile') gereksiz, profile User modelinde
        other_user = get_object_or_404(User, username=username)
        messages_qs = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user))
            # select_related sender ve receiver için yeterli, profile gerek yok
        ).select_related('sender', 'receiver').order_by('sent_at') 

        # Gelen mesajları okundu olarak işaretle
        Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
        
        form = MessageForm()
        
        # Profil resmini doğrudan other_user'dan al
        other_user_pic_url = None
        if other_user.profile_picture:
            other_user_pic_url = other_user.profile_picture.url
        else:
            from django.templatetags.static import static
            other_user_pic_url = static('images/default_avatar.png')
        
        context = {
            'other_user': other_user,
            'other_user_pic_url': other_user_pic_url,
            'messages': messages_qs,
            'form': form,
        }
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.partial_template_name, context, request=request)
            return HttpResponse(html)
            
        return render(request, self.template_name, context)

    def post(self, request, username):
        other_user = get_object_or_404(User, username=username)
        form = MessageForm(request.POST)
        if form.is_valid():
            # Formdan temizlenmiş veriyi al
            message_text = form.cleaned_data['text']
            
            # Message nesnesini manuel oluştur
            message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                text=message_text
            )

            # --- İlk Mesaj Kontrolü Başlangıcı ---
            is_first_message = Message.objects.filter(
                (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
            ).count() == 1
            # --- İlk Mesaj Kontrolü Sonu ---

            # Başarılı AJAX isteği için JSON yanıtı döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Mesaj bildirimi artık Notification tablosuna değil, Message tablosundaki is_read=False durumuna göre çalışacak
                # Bu nedenle burada bildirim oluşturmuyoruz
                     
                response_data = {
                    'success': True,
                    'sender': request.user.username,
                    'text': message_text,
                    'sent_at_relative': 'şimdi' # Göreceli zaman için basit gösterim
                }
                
                # Eğer ilk mesaj ise, yanıtı yönlendirme URL'si ile güncelle
                if is_first_message:
                    response_data['redirect_url'] = reverse('inbox')
                    print(f"İlk mesaj gönderildi. Yönlendirme URL'si eklendi: {response_data['redirect_url']}")

                return JsonResponse(response_data)
            
            # Normal POST isteği (JavaScript kapalıysa vb.)
            # İlk mesajsa yine inbox'a yönlendir
            if is_first_message:
                 return redirect('inbox')
            # Değilse mevcut sohbete yönlendir
            return redirect('conversation', username=username)
        else:
            # Hata durumunda tekrar formu ve mesajları göster
            existing_messages = Message.objects.filter(
                (Q(sender=request.user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=request.user))
            ).order_by('sent_at')
            
            # AJAX isteği için JSON hatası döndür
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Form hatalarını JSON\'a çevir (basit hali)
                error_dict = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({'success': False, 'errors': error_dict}, status=400)
            
            # Normal POST isteği hatası
            context = {
                'other_user': other_user,
                'messages': existing_messages,
                'form': form, # Hatalı formu geri gönder
            }
            messages.error(request, "Mesaj gönderilirken bir hata oluştu.")
            return render(request, self.template_name, context)

class LoadChatMessagesView(LoginRequiredMixin, View):
    """Belirli bir konuşmanın mesajlarını JSON olarak döndürür."""
    def get(self, request, conversation_id):
        try:
            conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            messages = ChatMessage.objects.filter(conversation=conversation).order_by('sent_at')
            # Mesajları JSON uyumlu hale getir
            message_data = [
                {
                    'sender_is_user': msg.sender_is_user,
                    'text': msg.text,
                    'sent_at': msg.sent_at.strftime('%d-%m-%Y %H:%M'), # İsteğe bağlı formatlama
                }
                for msg in messages
            ]
            return JsonResponse({'messages': message_data})
        except ChatConversation.DoesNotExist:
            return JsonResponse({'error': 'Konuşma bulunamadı veya yetkiniz yok.'}, status=404)
        except Exception as e:
             print(f"Mesaj yükleme hatası: {e}")
             return JsonResponse({'error': 'Mesajlar yüklenirken bir hata oluştu.'}, status=500)

class DeleteChatConversationView(LoginRequiredMixin, View):
    """Belirli bir konuşmayı siler."""
    def post(self, request, conversation_id):
        try:
            conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return JsonResponse({'success': True, 'message': 'Konuşma başarıyla silindi.'})
        except ChatConversation.DoesNotExist:
            return JsonResponse({'error': 'Konuşma bulunamadı veya yetkiniz yok.'}, status=404)
        except Exception as e:
            print(f"Konuşma silme hatası: {e}")
            return JsonResponse({'error': 'Konuşma silinirken bir hata oluştu.'}, status=500)

class RenameChatConversationView(LoginRequiredMixin, View):
    """Belirli bir konuşmayı yeniden adlandırır."""
    def post(self, request, conversation_id):
        try:
            data = json.loads(request.body)
            new_title = data.get('new_title')
            if not new_title:
                return JsonResponse({'error': 'Yeni başlık boş olamaz.'}, status=400)
            
            conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            conversation.title = new_title.strip()
            conversation.save()
            return JsonResponse({'success': True, 'message': 'Konuşma başarıyla yeniden adlandırıldı.', 'new_title': conversation.title})
        except ChatConversation.DoesNotExist:
            return JsonResponse({'error': 'Konuşma bulunamadı veya yetkiniz yok.'}, status=404)
        except json.JSONDecodeError:
             return JsonResponse({'error': 'Geçersiz JSON formatı.'}, status=400)
        except Exception as e:
            print(f"Konuşma yeniden adlandırma hatası: {e}")
            return JsonResponse({'error': 'Konuşma yeniden adlandırılırken bir hata oluştu.'}, status=500)

class CheckUserExistsAPIView(View):
    """Verilen kullanıcı adının sistemde olup olmadığını kontrol eder."""
    def get(self, request, username):
        exists = User.objects.filter(username=username).exists()
        profile_url = None
        if exists:
            # Kullanıcı varsa profil URL'ini de döndür
            profile_url = reverse('user_profile', kwargs={'username': username})
            
        return JsonResponse({'exists': exists, 'profile_url': profile_url})

# Kullanıcı mesajlaşmalarını silmek için yeni view (Artık gizleme yapıyor)
class DeleteMessageConversationView(LoginRequiredMixin, View):
    """İki kullanıcı arasındaki konuşmayı mevcut kullanıcı için gizler."""
    def post(self, request, username):
        try:
            other_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Kullanıcı bulunamadı.'}, status=404)
        
        user = request.user
        
        # Mesajları silmek yerine gizleme kaydı oluştur
        hidden_conv, created = UserHiddenConversation.objects.get_or_create(
            user=user,
            other_user=other_user
        )
        
        if created:
            message = f"{other_user.username} ile olan konuşmanız gizlendi."
            status = 'success'
            print(f"Konuşma gizlendi: {user.username} -> {other_user.username}")
        else:
            # Zaten gizlenmişse tekrar gizlemeye gerek yok, bilgi verelim
            message = f"{other_user.username} ile olan konuşmanız zaten gizli."
            status = 'info'
            print(f"Konuşma zaten gizliydi: {user.username} -> {other_user.username}")
            
        return JsonResponse({'status': status, 'message': message})

# Takipçi ve Takip Edilen Listeleri için View'lar
class FollowersListView(LoginRequiredMixin, ListView):
    template_name = 'follow_list.html'
    context_object_name = 'user_list'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Önce profil kullanıcısını bulalım
        try:
            self.profile_user = User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist:
            raise Http404("Kullanıcı bulunamadı.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Profil kullanıcısını takip edenleri (followers) listele
        return self.profile_user.followers.select_related('follower').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.profile_user
        context['page_title'] = f"{self.profile_user.username} Takipçileri"
        context['list_type'] = 'followers' # Template\'te başlık vb. için
        # Her kullanıcı için takip durumunu ekle (isteğe bağlı, performansı etkileyebilir)
        if self.request.user.is_authenticated:
            following_ids = set(self.request.user.following.values_list('followed_id', flat=True))
            for item in context['user_list']:
                item.current_user_is_following = item.follower_id in following_ids
        return context

class FollowingListView(LoginRequiredMixin, ListView):
    template_name = 'follow_list.html' # Aynı template\'i kullanabiliriz
    context_object_name = 'user_list'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        try:
            self.profile_user = User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist:
            raise Http404("Kullanıcı bulunamadı.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Profil kullanıcısının takip ettiklerini (following) listele
        # Takip edilen kullanıcı bilgilerini de çekmek için select_related('followed')
        return self.profile_user.following.select_related('followed').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.profile_user
        context['page_title'] = f"{self.profile_user.username} Takip Edilenler"
        context['list_type'] = 'following'
        
        # Her kullanıcı (takip edilen kişi) için mevcut kullanıcının takip durumunu ekle
        if self.request.user.is_authenticated:
            # Giriş yapmış kullanıcının takip ettiği TÜM kullanıcıların ID'lerini al
            following_ids = set(self.request.user.following.values_list('followed_id', flat=True))
            # user_list'teki her Follow nesnesi için
            for item in context['user_list']:
                # item.followed (takip edilen kişi) ID'si, giriş yapmış kullanıcının takip listesinde var mı?
                item.current_user_is_following = item.followed_id in following_ids
        return context

# Tüm Rozetleri Listeleyen View
class BadgesListView(ListView):
    template_name = 'badges_list.html'
    context_object_name = 'all_badges'
    ordering = ['category', 'tier_order', 'name']  # tier yerine tier_order ile sıralama

    def get_queryset(self):
        # Sadece aktif rozetleri göster ve tier_order ile sırala
        return Badge.objects.filter(is_active=True).order_by('category', 'tier_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Tüm Rozetler"
        # Giriş yapmış kullanıcının rozetlerini de context'e ekle
        if self.request.user.is_authenticated:
            context['user_badges'] = self.request.user.badges.filter(is_active=True)
            context['user_badge_ids'] = set(context['user_badges'].values_list('id', flat=True))
        else:
            context['user_badges'] = []
            context['user_badge_ids'] = set()
        return context

# Arama Sayfası AI Önerisi Yenileme View
class RefreshAISuggestionView(View):
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q')
        previous_suggestions_raw = request.GET.get('current_suggestions', '') # Bunu kullanacağız
        
        if not query:
            return JsonResponse({'error': 'Arama sorgusu eksik.'}, status=400)

        print(f"Yenileme isteği (Doğrudan API) - Query: {query}")
        
        # --- Doğrudan Gemini API Çağrısı (Yenileme) --- 
        try:
            # Sistem Talimatı (Yenileme odaklı - Daha Dinamik - Üçlü Tırnak Kullanımı)
            refresh_system_instruction = f"""Tekrar selam! '{query}' için radarlarıma takılan YENİ önerilerim var! 🚀 Önceki listede olmayan, taptaze seçenekler:

1. **@@Yeni Film/Dizi (Yıl)@@**
   *Bunu neden ekledim?* [Yepyeni, yine arkadaşça ve kişisel bir neden/yorum ekle].

2. **@@Başka Yeni Film/Dizi (Yıl)@@**
   *Şuna da bir göz at derim!* Çünkü [başka yeni, samimi bir neden/yorum ekle].

(5 tane olana kadar aynı formatta devam et)"""
            
            # Görev Tanımı (Daha Dinamik Son - Üçlü Tırnak Kullanımı)
            task_prompt = f"""Kullanıcı '{query}' araması için YENİ ve FARKLI öneriler istiyor. Bu konuyla ilgili, aşağıdaki listedekilerden **TAMAMEN FARKLI** 5 film/dizi öner.

**Önceki Öneriler (Bunları KESİNLİKLE önerme!):**
{previous_suggestions_raw}

**Yeni Öneriler:**

Tonun yine ÇOK arkadaş canlısı, samimi, esprili ve ENERJİK olsun. Başlıklar **@@Başlık (Yıl)@@** formatında, açıklamalar kısa, kişisel ve İÇTEN yorumlar içersin. 
Listeyi sunduktan sonra, yine sabit bir bitiş cümlesi yerine, '{query}' ile veya sinemayla ilgili kısa, arkadaşça bir kapanış yorumu ekle. Örneğin: 'Bu seferkiler tam senlik olabilir!', 'Daha fazla istersen söylemen yeterli! 😉', 'Keyifli keşifler!' gibi."""

            # Final Prompt
            final_prompt = f"{refresh_system_instruction}\n\n{task_prompt}"

            # Modeli başlat ve mesajı gönder (History yok)
            if not hasattr(ApiKey, 'model'):
                 raise Exception("Hata: ApiKey.py içinde 'model' nesnesi bulunamadı.")
             
            chat = ApiKey.model.start_chat(history=[])
            response = chat.send_message(final_prompt)

            # Yanıtı işle
            if response.candidates:
                ai_suggestion_markdown = response.text
                # @@ işaretlerini ** ile değiştir
                processed_markdown = ai_suggestion_markdown.replace('@@', '**')
                ai_suggestion_html = convert_markdown_to_html(processed_markdown)
                
                return JsonResponse({
                    'success': True, 
                    'suggestion_html': ai_suggestion_html,
                    'suggestion_markdown': ai_suggestion_markdown 
                })
            else:
                print("Gemini Yanıtı Engellendi/Boş (RefreshView):", response.prompt_feedback)
                return JsonResponse({'error': 'AI önerisi alınırken bir sorun oluştu (Engellendi/Boş).'}, status=500)
                
        except Exception as e:
            print(f"Doğrudan AI önerisi yenileme hatası: {e}")
            return JsonResponse({'error': 'AI önerisi yenilenirken bir hata oluştu.'}, status=500)
