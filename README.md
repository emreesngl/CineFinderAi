<div align="center">
  <!-- Eğer projenize ait güzel bir logonuz varsa alttaki linki güncelleyebilirsiniz. Şimdilik geçici bir logo simgesi konulmuştur -->
  <h1>🎬 CineFinder AI</h1>
  <strong>Akıllı Sinema Asistanınız ve Sosyal Film Platformunuz</strong>

  <br><br>

  [![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-5.x-092E20.svg)](https://www.djangoproject.com/)
  [![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC.svg)](https://tailwindcss.com/)
  [![Gemini API](https://img.shields.io/badge/Gemini_API-AI-FF6F00.svg)](https://deepmind.google/technologies/gemini/)
  [![TMDB API](https://img.shields.io/badge/TMDB_API-Movies-01B4E4.svg)](https://www.themoviedb.org/)
  
</div>

<br />

## 🌟 Hakkında

**CineFinder AI**, film ve dizi tutkunları için geliştirilmiş son derece zengin veriye sahip interaktif bir sosyal medya ve keşif platformudur. [The Movie Database (TMDB)](https://www.themoviedb.org/) API desteğiyle dünya üzerindeki sayısız görsel yapıma, oyunculara ve vizyon tarihlerine ulaşırken; içerisinde barındırdığı Google Gemini destekli **Filmbot** AI sohbet asistanı ile zevkinize uygun en isabetli filmleri saniyeler içinde doğal ve eğlenceli bir sohbet eşliğinde bulmanızı sağlar!

## ✨ Öne Çıkan Özellikler

- 🤖 **Akıllı Filmbot (Gemini AI):** Sizinle bir sinema eleştirmeni edasıyla sohbet eden, zevklerinizi anlayan ve akıllı algoritmalarla direkt nokta atışı dizi/film tavsiyeleri sunan asistan.
- 🎥 **Sınırsız Veritabanı:** TMDB'den çekilen zengin anlık bilgiler sayesinde; vizyondaki filmler, popüler diziler, oyuncular, ayrıntılı özetler ve fragmanlar keşfetmeniz için hazırdır.
- 🧑‍🤝‍🧑 **Sosyal Etkileşim:** Diğer kullanıcıları bulun, takip edin, *anlık sohbet mesajlarıyla* haberleşin, veya sinema dünyası dedikodularını yapın!
- 🏆 **Oyunlaştırma (Gamification):** Platform üzerinde izlediğiniz filmlere yorum yaptıkça, onlara (1-10) arasında puan verdikçe deneyim puanı (**XP**) kazanır, **seviye atlar** ve profilinize benzersiz **Rozetler (Badges)** eklersiniz.
- 📋 **Kişisel Koleksiyonlar:** "Favoriler", "İzleyeceklerim", ve "Takiplerim" gibi özel listeler oluşturup yöneterek kendinize dinamik bir dijital sinema vitrini kurun.
- 🔐 **Güvenli Kimlik Doğrulama:** Django-Allauth entegrasyonu yardımıyla klasik kullanıcı adı ve güvenli şifrelerin yanı sıra; sadece tek tıkla **Google OAuth** kullanarak giriş imkanı.
- 🚀 **Performans Odaklı Altyapı:** Yerel bellekte otomatik `caching` yapan entegre önbellek altyapısı ve ileri düzey `Supabase PostgreSQL` veritabanı ile bulutta kusursuz çalışma.

---

## 🛠️ Kullanılan Teknolojiler

| Kategori | Teknoloji |
| :--- | :--- |
| **Backend** | Python, Django 5.x |
| **Frontend** | HTML5, Vanilla JavaScript, TailwindCSS, Bootstrap 5 (Crispy Forms) |
| **Database** | SQLite (Geliştirme / Local), Supabase PostgreSQL (Prodüksiyon / Canlı) |
| **APIs** | TMDB API, Google Generative AI (Gemini 1.5 Pro) |

---

## 🚀 Kurulum (Local Development)

Projeyi kendi bilgisayarınızda kurmak ve geliştirmek için aşağıdaki adımları sırasıyla uygulayabilirsiniz.

### 1. Ön Koşullar
- Python 3.9 veya daha yenisi

### 2. Repoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/CineFinderAi.git
cd CineFinderAi
```

### 3. Sanal Ortam (Virtual Environment) Başlatın
Sanal ortam oluşturarak sisteminizde yüklü kütüphaneler ile proje kütüphanelerinin çakışmasını engelleyin.
```bash
python -m venv venv

# Windows kullanıyorsanız aktivasyon kodu:
venv\Scripts\activate

# Mac/Linux kullanıyorsanız aktivasyon kodu:
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin (Requirements)
```bash
pip install -r requirements.txt
```

### 5. .env (Çevresel Değişkenler) Dosyasını Kurun
Projeyi API'ler ile bağlamak adına repoda sizin için bırakılmış **`.env.example`** dosyasının kopyasını çıkarıp ismini **`.env`** olarak değiştirin. Çıkardığınız dosyanın içerisine oluşturduğunuz keylerinizi girin.
> **Not:** Ücretsiz olarak [Google AI Studio](https://aistudio.google.com/)'dan Gemini anahtarı, ve [TMDB Developer](https://developer.themoviedb.org/docs/getting-started)'dan TMDB arama/veri anahtarınızı temin edebilirsiniz.


### 6. Veritabanını ve Tabloları İşleyin
Projeyi ilk defa açarken boş bir veritabanı kurmalısınız, aşağıdaki komutlarla tabloları inşa edebilirsiniz.
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Sunucuyu Ayağa Kaldırın
```bash
python manage.py runserver
```
Artık tarayıcınızdan `http://localhost:8000` adresine giderek platformu yerel ağınızda test edebilirsiniz! 🎉

---

## 📸 Ekran Görüntüleri 
*Bu kısmı projenizi Github'a yükledikten sonra, projenin arayüz fotoğraflarını direkt bu README dosyası içerisine sürükleyip bırakarak güncelleyebilirsiniz. Dışarıdan bakan birinin projeyi canlı görebilmesi için buraya arayüz resimleri yüklemeniz şiddetle tavsiye edilir.*

<p float="left">
  <img src="https://via.placeholder.com/400x250.png?text=Buras%C4%B1+%C4%B0%C3%A7in+Ana+Sayfa+%28Home%29+Foto%C4%9Fraf%C4%B1+Ekleyin" width="49%" />
  <img src="https://via.placeholder.com/400x250.png?text=Filmbot+AI+Sohbet+K%C4%B1sm%C4%B1+Foto%C4%9Fraf%C4%B1" width="49%" /> 
</p>


## 🤝 Katkıda Bulunma
Katkılarınız bizim için her zaman çok önemli! Bu projeyi geliştirirken bir modül eklemek veya bir "bug" çözmek isterseniz:
1. Bu projeyi kendi profilinizde **Fork**'layın.
2. Yeni özellik / geliştirme için kendi sisteminizde bir branch açın (`git checkout -b feature/MuthisSohbetSayfasi`).
3. Değişikliklerinizi işleyin (`git commit -m '"MuthisSohbetSayfasi" ile animasyonlar eklendi.'`).
4. Reponuza push'layın (`git push origin feature/MuthisSohbetSayfasi`).
5. Bu repoya bir **Pull Request (PR)** açarak inceleme gönderin.

---
**Geliştirici:** [*https://github.com/emreesngl*](https://github.com/emreesngl)  
*Sinema, algoritma ve yapay zeka büyüsü eklenerek yapılmıştır 🎬🍿🔥*
