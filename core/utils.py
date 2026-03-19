import requests
from django.conf import settings
import google.generativeai as genai
import ApiKey # ApiKey.py dosyasını import et
import os # os modülünü import et

TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/'

# Ortam değişkeninden Gemini API anahtarını al
# Bu satırı settings.py'den almak yerine doğrudan os.getenv ile alalım
# Belki settings.py cache'leniyor olabilir.
ACTUAL_GEMINI_KEY = os.getenv('GEMINI_API_KEY')
# print(f"--- DEBUG: Kullanılan Gemini API Anahtarı: {ACTUAL_GEMINI_KEY} ---") # Anahtarı yazdırmayı kaldır

# GEMINI_API_KEY = settings.GEMINI_API_KEY # Bu satırı yorum satırı yapabilir veya silebiliriz
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)
# else:
#     print("Uyarı: GEMINI_API_KEY .env dosyasında tanımlı değil!")

# Yeni anahtarla yapılandır
if ACTUAL_GEMINI_KEY:
    genai.configure(api_key=ACTUAL_GEMINI_KEY)
else:
    print("Uyarı: GEMINI_API_KEY ortam değişkeni bulunamadı!")

def get_tmdb_config():
    """TMDB API yapılandırmasını (resim URL'leri vb.) alır."""
    url = f"{TMDB_BASE_URL}/configuration"
    params = {'api_key': TMDB_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # HTTP hatası varsa exception fırlat
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB config alınırken hata: {e}")
        return None

# İhtiyaç duyulursa kullanılmak üzere yapılandırmayı başta alabiliriz
# tmdb_config = get_tmdb_config()
# image_base_url = tmdb_config.get('images', {}).get('secure_base_url', TMDB_IMAGE_BASE_URL)
# poster_size = tmdb_config.get('images', {}).get('poster_sizes', ['w500'])[3] # Genellikle w500 iyi bir boyuttur

def get_poster_url(path, size='w500'):
    """Verilen path ve boyut için tam poster URL'sini döndürür."""
    if not path:
        return None # Veya varsayılan bir resim URL'si
    return f"{TMDB_IMAGE_BASE_URL}{size}{path}"

def search_media(query, media_type='multi'):
    """Film, dizi veya her ikisi için arama yapar (media_type: movie, tv, multi)."""
    url = f"{TMDB_BASE_URL}/search/{media_type}"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'tr-TR', # Sonuçları Türkçe almayı deneyelim
        'include_adult': False,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB arama hatası ({query}): {e}")
        return []

def get_media_details(media_id, media_type='movie'):
    """Belirli bir film veya dizi detayını alır."""
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'append_to_response': 'credits,videos,similar,images' # Oyuncular, videolar, benzerler, resimler
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # --- LOGLAMA EKLE --- 
        print(f"--- TMDB API Yanıtı ({media_type}/{media_id}) ---")
        if 'videos' in data:
            print(f"Video Anahtarı: Mevcut, Sonuç Sayısı: {len(data['videos'].get('results', []))}")
        else:
            print("Video Anahtarı: API Yanıtında BULUNAMADI!")
        print("-------------------------")
        # --- LOGLAMA SONU ---
        return data
    except requests.exceptions.RequestException as e:
        print(f"TMDB detay hatası ({media_type}/{media_id}): {e}")
        return None

def get_popular_media(media_type='movie', page=1):
    """Popüler filmleri veya dizileri belirli bir sayfadan alır."""
    url = f"{TMDB_BASE_URL}/{media_type}/popular"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'page': page # Sayfa parametresi eklendi
        }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB popüler {media_type} sayfa {page} hatası: {e}")
        return []

def get_upcoming_movies(page=1):
    """Yakında çıkacak filmleri alır."""
    url = f"{TMDB_BASE_URL}/movie/upcoming"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'page': page
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB yakında çıkacaklar hatası: {e}")
        return []

def get_now_playing_movies(page=1):
    """Şu an vizyonda olan filmleri alır."""
    url = f"{TMDB_BASE_URL}/movie/now_playing"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'page': page
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB vizyondakiler hatası: {e}")
        return []

def get_top_rated_media(media_type='movie', page=1):
    """En yüksek puanlı filmleri veya dizileri alır."""
    url = f"{TMDB_BASE_URL}/{media_type}/top_rated"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'page': page
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB en iyiler hatası: {e}")
        return []

def discover_media_by_genre(genre_id, media_type='movie', page=1):
    """Belirli bir türe göre film veya dizi keşfini sağlar."""
    url = f"{TMDB_BASE_URL}/discover/{media_type}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'with_genres': genre_id,
        'page': page
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB tür keşfi hatası: {e}")
        return []

def get_trailer_key(media_id, media_type='movie'):
    """Medya için YouTube fragman anahtarını bulur."""
    details = get_media_details(media_id, media_type)
    if details and 'videos' in details and details['videos']['results']:
        for video in details['videos']['results']:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return video['key']
    return None

def get_tmdb_genres(media_type='movie'):
    """TMDB'den film veya dizi türlerini alır."""
    url = f"{TMDB_BASE_URL}/genre/{media_type}/list"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('genres', [])
    except requests.exceptions.RequestException as e:
        print(f"TMDB tür listesi hatası: {e}")
        return []

def get_tmdb_countries():
    """TMDB'den ülke listesini alır."""
    url = f"{TMDB_BASE_URL}/configuration/countries"
    params = {'api_key': TMDB_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        # Ülkeleri iso_3166_1 koduna göre filtreleyip döndürelim
        countries = response.json()
        # Bazı popüler veya sık kullanılan ülkeleri öne alabiliriz (isteğe bağlı)
        # Örneğin: TR, US, GB, DE, FR, ES, IT, JP, KR, IN
        preferred_codes = ['TR', 'US', 'GB', 'DE', 'FR', 'ES', 'IT', 'JP', 'KR', 'IN', 'CA', 'AU', 'BR', 'CN', 'RU']
        sorted_countries = sorted(
            countries,
            key=lambda x: (x['iso_3166_1'] not in preferred_codes, x.get('native_name', x['english_name']))
        )
        return sorted_countries
    except requests.exceptions.RequestException as e:
        print(f"TMDB ülke listesi hatası: {e}")
        return []

def get_tmdb_watch_providers(media_type='movie', region='TR'):
    """TMDB'den watch providers listesini alır."""
    url = f"{TMDB_BASE_URL}/watch/providers/{media_type}"
    params = {
        'api_key': TMDB_API_KEY,
        'watch_region': region
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        providers = response.json().get('results', [])
        
        # Logo URL'lerini tam hale getir
        for provider in providers:
            if provider.get('logo_path'):
                provider['logo_url'] = get_poster_url(provider['logo_path'], 'w92')
        
        return providers
    except requests.exceptions.RequestException as e:
        print(f"TMDB watch providers hatası: {e}")
        return []

def generate_gemini_response(user_message, history=None):
    """Gemini API ile yanıt üretir, konuşma geçmişini ve TMDB verilerini kullanır.
    
    Args:
        user_message (str): Kullanıcının son mesajı.
        history (list, optional): Gemini formatında mesaj geçmişi. 
                                  Örn: [{'role': 'user', 'parts': [{'text': '...'}]}]
    
    Returns:
        dict: {'text': ai_response_text}
    """
    if not hasattr(ApiKey, 'model'):
        print("Hata: ApiKey.py içinde 'model' nesnesi bulunamadı.")
        # Sözlük formatında döndür
        return {'text': "AI modeli yapılandırılamadığı için yanıt üretilemiyor."}

    try:
        # Sistem talimatı (Botun kişiliği ve genel davranışları)
        system_instruction = (
            "Sen Filmbot adında, film ve diziler konusunda TUTKULU, bilgili, esprili, arkadaş canlısı ve ÇOK yardımsever bir sohbet asistanısın. "
            "Gayriresmi, doğal ve AKICI bir dil kullan. İnsanlarla sohbet eder gibi konuş. "
            "SENİN GÖREVİN: Konu ne olursa olsun, sohbeti MUTLAKA filmlere ve dizilere bağlamak! Kullanıcı sana kitaptan mı bahsetti? Hemen filmi/dizisi var mı diye kontrol et veya 'Bu kitabın atmosferi bana şu filmi hatırlattı...' de. Hava durumunu mu sordu? 'Tam evde battaniye altında film/dizi izlemelik bir hava!' gibi yanıtlar ver. Tarihten mi bahsediyor? O dönemi anlatan bir film/dizi öner. HER KONUDA sinematik bir bağlantı kur."
            "Kullanıcının sorularına DETAYLI cevap ver, film/dizi önerilerinde bulun. Önerilerini yaparken ASLA sadece listeleme. Neden önerdiğini, filmin/dizinin atmosferini, ilginç bir detayını, sana hissettirdiklerini ekleyerek YORUM KAT. Duygusal ve coşkulu olabilirsin."
            "Film veya dizi listeleri sunarken ŞU FORMATI KULLAN (Markdown):"
            "1. **Film/Dizi Adı (Orijinal Adı Varsa):** Hemen alt satıra geçerek film/dizi hakkındaki yorumunu, neden önerdiğini veya ilginç detayları yaz."
            "2. **Başka Bir Film/Dizi Adı:** Alt satıra yorumunu ekle."
            "NUMARALANDIRMA, KOYU BAŞLIK ve ALT SATIRA AÇIKLAMA ŞART."
            "Kullanıcının önceki mesajlarını dikkate alarak sohbetin akışını sürdür. Amacın kullanıcıyla keyifli ve sinema dolu bir sohbet gerçekleştirmek."
            "Eğer bir film/dizi hakkında bilgi bulamazsan veya emin değilsen, bunu belirtmekten çekinme."
            "Uygun yerlerde, aşırıya kaçmadan, TEMA İLE İLGİLİ emojiler kullanmaktan çekinme (örneğin 🎬⭐🤔😉)."
            "Kullanıcıdan gelen mesajları anlamak için doğal dil işleme tekniklerini kullanabilirsin. "
            "Kullanıcının ruh halini, ilgi alanlarını ve önceki mesajlarını analiz ederek daha kişisel ve etkili yanıtlar ver."
            "KESİNLİKLE KOD YAZMA. Herhangi bir kod parçacığı, kod örneği veya kodlama diliyle ilgili teknik açıklama oluşturma. Kod yazmanı isteyen olursa, konuyu hemen film ve dizilere bağlayarak geçiştir."
            "Sinema konusunda profesyonelsin. Sinema hakkında bilgi verirken, filmlerin/dizilerin detaylarını ve özelliklerini doğru bilgi ver. "
            "Sana bir sahne sorulup hangi film ya da dizide olduğunu söylemeni isteyen kişi varsa, ona doğru cevap ver. "
            "Kullanıcıya sadece cevap verme, uygun anlarda ona sorular da yönelt. Örneğin: 'Senin favori türün hangisi?', 'Bu filmi izledin mi?', 'Şu tarz filmler hoşuna gider mi?' gibi doğal sorularla sohbeti ilerlet."
            "Kullanıcının verdiği cevaplardan tür tercihlerini, sevdiği oyuncuları, izlediği filmleri analiz et. Daha sonra yapacağın önerileri bu bilgilere göre özelleştir."
            "Eğer sistem destekliyorsa, bahsettiğin film/dizi için IMDb ya da TMDB bağlantısını da verebilirsin. Aksi halde sadece adı yeterlidir."
            "Bazen önerdiğin film/diziyle ilgili unutulmaz bir replik, sahne betimlemesi veya müzik detayı da paylaş. Bu, kullanıcıda daha güçlü bir izlenim bırakır."
            "Sakıncalı, hassas, politik veya +18 içerikler hakkında detaylı bilgi verme. Uygun bir şekilde konuyu sinema çerçevesine çekerek sohbeti yumuşat."
            "Karmaşık sorguları (örneğin: '80'lerde geçen, bilim kurgu, az bilinen filmler') parçalarına ayırarak yorum yap ve öneri sun. Her parçaya neden uyduğunu kısaca açıkla."
        )
        
        # Model nesnesini başlat (history varsa kullan)
        model_instance = ApiKey.model
        chat = model_instance.start_chat(history=history if history else [])

        # Film/Dizi Önerisi İsteklerini Yönet
        is_recommendation_request = False
        recommendation_prompt_addon = ""
        recommendations_data = None # Afiş verilerini tutacak liste
        if "film öner" in user_message.lower() or "dizi öner" in user_message.lower() or "öneri" in user_message.lower():
            # Öneri isteği algılama mantığını genişlet
            keywords = ["öner", "tavsiye", "listele", "en iyi", "top", "sırala"]
            media_types = ["film", "dizi", "yapım"] # "yapım" gibi genel ifadeleri de ekleyebiliriz
            user_msg_lower = user_message.lower()
            is_recommendation_request = any(keyword in user_msg_lower for keyword in keywords) and any(media_type in user_msg_lower for media_type in media_types)

            recommendation_prompt_addon = "" # Başlangıçta boş
            recommendations_data = None      # Başlangıçta None

            if is_recommendation_request:
                # Hangi medya tipi istendiğini belirle (öncelik dizi, sonra film, sonra genel)
                media_type = "tv" if "dizi" in user_msg_lower else "movie" if "film" in user_msg_lower else "movie" # Varsayılan film olabilir

                # Tür belirtilmiş mi kontrol et
                genres = get_tmdb_genres(media_type)
                requested_genre_id = None
                requested_genre_name = None # Gemini prompt'u için tür adını sakla
                import re # Regex için import et
                for genre in genres:
                    # Daha sağlam tür eşleşmesi (Türkçe karakterler ve kelime sınırları)
                    if re.search(r'\\b' + re.escape(genre['name'].lower()) + r'\\b', user_msg_lower):
                        requested_genre_id = genre['id']
                        requested_genre_name = genre['name']
                        break

                # Hangi TMDB fonksiyonunu çağıracağımıza karar ver
                if "en iyi" in user_msg_lower or "top" in user_msg_lower:
                    print(f"--- TMDB Request: Getting top rated {media_type} ---")
                    results = get_top_rated_media(media_type)
                    request_description = f"en iyi {media_type} listesi" # Prompt için
                elif requested_genre_id:
                    print(f"--- TMDB Request: Discovering {media_type} by genre ID {requested_genre_id} ({requested_genre_name}) ---")
                    results = discover_media_by_genre(requested_genre_id, media_type)
                    request_description = f"{requested_genre_name} türünde {media_type} önerisi" # Prompt için
                else:
                    # Yeni/Yakın tarihli istenmiş mi? (Sadece filmler için mantıklı)
                    if media_type == "movie" and ("yeni" in user_msg_lower or "yakın" in user_msg_lower or "vizyon" in user_msg_lower):
                        print("--- TMDB Request: Getting upcoming and now playing movies ---")
                        upcoming = get_upcoming_movies()
                        now_playing = get_now_playing_movies()
                        # Popülerleri de ekleyerek çeşitlendirelim
                        popular = get_popular_media(media_type)
                        # Tekrarları önlemek için ID set'i kullanalım
                        seen_ids = set()
                        combined_results = []
                        for r_list in [now_playing, upcoming, popular]:
                            for item in r_list:
                                if item['id'] not in seen_ids:
                                    combined_results.append(item)
                                    seen_ids.add(item['id'])
                        results = combined_results
                        request_description = f"yeni/vizyondaki {media_type} önerisi" # Prompt için
                    else:
                        # Varsayılan: Popülerleri getir
                        print(f"--- TMDB Request: Getting popular {media_type} ---")
                        results = get_popular_media(media_type)
                        request_description = f"popüler {media_type} önerisi" # Prompt için

                top_results = results[:5] # Öneri sayısını 5 ile sınırlayalım

                if top_results:
                    # recommendations_data ve simple_recommendations_list'i TÜM top_results için oluştur
                    simple_recommendations_list = [] # Prompt için liste
                    for media in top_results:
                        tmdb_id = media.get('id')
                        title = media.get('title', media.get('name', 'İsimsiz'))
                        year = media.get('release_date', media.get('first_air_date', ''))[:4] if media.get('release_date', media.get('first_air_date', '')) else ''

                        # Prompt listesine ekle
                        simple_recommendations_list.append(f"{title} ({year})")

                    # Gemini'ye gidecek prompt eklentisi
                    simple_list_str = ", ".join(simple_recommendations_list)
                    recommendation_prompt_addon = (
                        f"Kullanıcı '{request_description}' istedi ('{user_message}'). Filmbot olarak TMDB'den şu potansiyel önerileri buldum (bunları yorumla): [{simple_list_str}].\\n\\n"
                        f"Şimdi, bu listedeki filmleri/dizileri kullanıcıya sunarken LÜTFEN sistem talimatlarında sana öğrettiğim gibi davran:\\n"
                        f"1. Her bir öneriyi **NUMARALI LİSTE** şeklinde sun.\\n"
                        f"2. Film/Dizi adını **KOYU** yaz (**Film Adı (Yıl)** gibi).\\n"
                        f"3. Yorumunu KOYU BAŞLIĞIN hemen ALTINDAKİ YENİ SATIRA yaz (`\\n` kullan).\\n"
                        f"4. **ÇOK ÖNEMLİ:** Yorumların **SADECE VE SADECE** sana az önce parantez içinde verdiğim şu listedeki [{simple_list_str}] filmler/diziler hakkında olsun. Bu listenin DIŞINDAKİ hiçbir filmden veya diziden KESİNLİKLE BAHSETME. Sadece sana verdiğim listedekileri yorumla.\\n"
                        f"Örnek formatı hatırla: \\n1. **Film Adı (Yıl)**\\nAçıklaman buraya...\\n2. **Diğer Film (Yıl)**\\nDiğer açıklama...\\n\\n"
                        f"Bu formatı KULLANARAK ve SADECE sana verilen listedeki her bir film/dizi için kendi ÖZGÜN yorumunu katarak, konuşkan ve samimi bir dille yanıt ver. Yorumun önemli!"
                    )
                else:
                    # Sonuç bulunamama durumu
                    recommendation_prompt_addon = f"Kullanıcı '{user_message}' ile bir istekte bulundu ancak bu kritere uygun film/dizi bulamadım. Bunu kibarca belirt ve başka bir tür veya kriter sormasını öner."

        # else: # Öneri isteği değilse, bu bloğa gerek yok, addon ve data zaten başlangıç değerlerinde

        # Gemini'ye gönderilecek son prompt
        final_prompt_parts = [system_instruction]
        if recommendation_prompt_addon:
            final_prompt_parts.append(recommendation_prompt_addon)
        # Kullanıcı mesajını her zaman ekle
        final_prompt_parts.append(f"\\nKullanıcının son mesajı: \\\"{user_message}\\\"\\nYanıtın:")
        final_prompt = "\\n".join(final_prompt_parts)

        # Mesajı gönder ve yanıtı al
        print("\\n--- Sending Prompt to Gemini ---")
        print("Prompt Addon Included:", bool(recommendation_prompt_addon))
        print("-----------------------------")
        response = chat.send_message(final_prompt)

        # --- DEBUG: Ham Gemini Yanıtını Yazdır ---
        print("\\n--- Raw Gemini Response Text ---")
        if response.candidates:
            print(response.text)
        else:
            print("No response text available (Blocked/Error)")
        print("-------------------------------")
        # --- DEBUG SONU ---

        # Güvenlik kontrolü
        if not response.candidates:
            print("Gemini Yanıtı Engellendi:", response.prompt_feedback)
            return {'text': "İsteğinizi işlerken bir sorun oluştu. Lütfen biraz daha farklı bir şekilde sormayı deneyin."}

        # Sonucu sözlük olarak döndür (Sadece metin)
        return {'text': response.text}

    except Exception as e:
        print(f"Gemini API hatası: {e}")
        # Sözlük formatında döndür
        return {'text': "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar dene."}

def discover_media(media_type='movie', params=None):
    """Filtre ve sıralama seçenekleriyle film veya dizi keşfini sağlar."""
    url = f"{TMDB_BASE_URL}/discover/{media_type}"
    
    default_params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'sort_by': 'popularity.desc',
        'page': 1,
        'include_adult': False,
        'vote_count.gte': 100 # Çok az oy almış sonuçları filtreleyelim (isteğe bağlı)
    }
    
    # Gelen parametreleri işle
    if params:
        # Sayfa numarasını int yap
        if 'page' in params:
            params['page'] = int(params.get('page', 1))
            
        # Türleri işle (virgülle ayrılmış string bekleniyor)
        if 'with_genres' in params and isinstance(params['with_genres'], list):
            # Boş stringleri filtrele (checkbox seçilmediğinde gelebilir)
            valid_genres = [g for g in params['with_genres'] if g]
            if valid_genres:
                 params['with_genres'] = ','.join(valid_genres)
            else:
                del params['with_genres'] # Boşsa parametreyi kaldır
            
        # Yıl parametrelerini ayarla (Film vs Dizi)
        if 'year_gte' in params and params['year_gte']: # Boş değilse
            year_param_gte = 'primary_release_date.gte' if media_type == 'movie' else 'first_air_date.gte'
            default_params[year_param_gte] = f"{params['year_gte']}-01-01"
            #del params['year_gte'] # Orijinal parametreyi kaldır (Güncellemede kalsın)
        if 'year_lte' in params and params['year_lte']: # Boş değilse
            year_param_lte = 'primary_release_date.lte' if media_type == 'movie' else 'first_air_date.lte'
            default_params[year_param_lte] = f"{params['year_lte']}-12-31"
            #del params['year_lte'] # Orijinal parametreyi kaldır (Güncellemede kalsın)

        # Puan parametreleri (boş değilse ekle)
        if 'vote_average.gte' in params and params['vote_average.gte']:
             default_params['vote_average.gte'] = params['vote_average.gte']
        if 'vote_average.lte' in params and params['vote_average.lte']:
             default_params['vote_average.lte'] = params['vote_average.lte']
        if 'vote_count.gte' in params and params['vote_count.gte']:
             default_params['vote_count.gte'] = params['vote_count.gte']
             
        # Süre parametreleri (sadece filmler için)
        if media_type == 'movie':
            if 'runtime.gte' in params and params['runtime.gte']:
                default_params['with_runtime.gte'] = params['runtime.gte']
            if 'runtime.lte' in params and params['runtime.lte']:
                default_params['with_runtime.lte'] = params['runtime.lte']
             
        # Ülke parametresi (boş değilse ekle)
        if 'with_origin_country' in params and params['with_origin_country']:
            default_params['with_origin_country'] = params['with_origin_country']

        # Platform parametresi (boş değilse ekle)
        if 'with_watch_providers' in params and params['with_watch_providers']:
            default_params['with_watch_providers'] = params['with_watch_providers']
            # Platform filtresi için bölge belirtmek gerekiyor (Türkiye için TR)
            default_params['watch_region'] = 'TR'

        # Parametreleri güncelle (sadece defaultta olmayanları veya değiştirilecekleri)
        default_params.update(params)
    
    # API çağrısı için gereksiz/uyumsuz parametreleri temizle (örn: yıl aralığı için kullandıklarımız)
    default_params.pop('year_gte', None)
    default_params.pop('year_lte', None)
    
    print("\n--- TMDB API Request ---")
    print("Endpoint:", url)
    print("Parameters:", default_params)
    # print("TMDB API Params:", default_params) # Debug için eklendi - Eski print yerine daha detaylısı

    try:
        response = requests.get(url, params=default_params)
        print("API Status Code:", response.status_code)
        response.raise_for_status()
        # API'den gelen toplam sayfa ve sonuç sayısını da döndürelim (Paginator için)
        data = response.json()
        print("API Response Snippet:", str(data)[:500]) # Yanıtın başını yazdır
        # print("Full API Response:", data) # Gerekirse tüm yanıtı görmek için
        print("------------------------\n")
        return {
            'results': data.get('results', []),
            'total_pages': data.get('total_pages', 1),
            'total_results': data.get('total_results', 0)
        }
    except requests.exceptions.RequestException as e:
        print(f"TMDB discover hatası: {e}")
        # Hata durumunda yanıtı da yazdırmaya çalışalım
        if 'response' in locals() and response is not None:
            print("Error Response Status:", response.status_code)
            try:
                print("Error Response Body:", response.text[:500])
            except Exception as read_err:
                print("Error reading response body:", read_err)
        print("------------------------\n")
        return {'results': [], 'total_pages': 1, 'total_results': 0} 