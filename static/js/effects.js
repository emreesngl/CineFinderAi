// Görsel Efektler JS

// Mouse Hareketine Duyarlı Efektler
document.addEventListener('DOMContentLoaded', function() {
  const parlakEfektler = document.querySelectorAll('.parlak-efekt'); // Efektleri başta seç

  // Mouse hareketi efektleri
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    const mouseX = e.clientX;
    const mouseY = e.clientY;
    
    // Işık hüzmesi mouse takibi (varsa)
    const huzmeler = document.querySelectorAll('.isik-huzmesi, .central-light-beam'); // .central-light-beam eklendi
    huzmeler.forEach(huzme => {
        // Sadece yatay ışık hüzmeleri dönsün
        if (!huzme.classList.contains('central-light-beam')) { 
            huzme.style.transform = `rotate(${35 + x * 5}deg) translateY(${y * 10}px)`;
            huzme.style.opacity = 0.4 + (x * 0.2);
        }
    });
    
    // Parlak efektleri fareyi takip etsin
    parlakEfektler.forEach((efekt, index) => {
        // Efektleri biraz gecikmeli veya farklı yönlerde hareket ettirebiliriz
        const moveX = mouseX - (efekt.offsetWidth / 2); // Merkeze al
        const moveY = mouseY - (efekt.offsetHeight / 2);
        // Basit takip:
        efekt.style.transform = `translate(${moveX}px, ${moveY}px)`;
        // Farklı efektler için farklı gecikme/yön eklenebilir:
        // if (index === 0) { efekt.style.transform = `translate(${moveX * 0.9}px, ${moveY * 0.9}px)`; }
        // else { efekt.style.transform = `translate(${moveX * 1.1}px, ${moveY * 1.1}px)`; }
    });

    // Panel gölge efekti (varsa)
    const paneller = document.querySelectorAll('.panel');
    paneller.forEach(panel => {
        // Basit bir parlama efekti ekleyebiliriz veya aşağıdaki gibi bırakabiliriz
        // panel.style.boxShadow = `${(x - 0.5) * -20}px ${(y - 0.5) * -10}px 150px rgba(79, 70, 229, ${0.1 + y * 0.1})`; // Örnek: Mor/Mavi tonlu
    });
  });

  // Sayfa Kaydırma Efektleri - Kartlar için
  const observerOptions = {
    root: null, // viewport
    rootMargin: '0px',
    threshold: 0.1 // %10 görünür olduğunda tetikle
  };

  const observerCallback = (entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('scroll-visible');
        observer.unobserve(entry.target); // Bir kere görününce izlemeyi bırak
      } 
    });
  };

  const scrollObserver = new IntersectionObserver(observerCallback, observerOptions);

  // Animasyon uygulanacak panelleri seç
  // Not: Ana arama bölümündeki panel hariç tutulabilir veya farklı animasyon uygulanabilir.
  const animatedPanels = document.querySelectorAll('.grid .panel'); // Sadece grid içindeki paneller
  animatedPanels.forEach(panel => {
    panel.classList.add('scroll-hidden'); // Başlangıçta gizli
    scrollObserver.observe(panel);
  });

  // Arka plan opaklık efekti (isteğe bağlı, çok fazla efekt varsa kaldırılabilir)
  /*window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    const opacity = Math.max(0, 1 - scrollY / 500);
    
    const arkaplan = document.querySelector('.arka-plan'); // base.html'deki main
    if (arkaplan) {
      arkaplan.style.opacity = opacity;
    }
  });*/
});

// ÖNEMLİ: Bu JS dosyasının base.html'deki inline tema değiştirme script'inden *sonra* yüklendiğinden emin olun.
// Eğer önce yüklenirse, DOMContentLoaded inline script çalışmadan tetiklenebilir. 