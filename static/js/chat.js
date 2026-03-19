// DOM elemanları
const chatSidebar = document.querySelector('.chat-sidebar');
const chatContainer = document.querySelector('.chat-container');
const emptyScreen = document.querySelector('.empty-screen');
const messageContainer = document.querySelector('.message-container');
const messageInput = document.querySelector('.message-input');
const sendButton = document.querySelector('.send-button');
const newChatButton = document.querySelector('.new-chat-button');
const chatHistory = document.querySelector('.chat-history');
const typingIndicator = document.querySelector('.typing-indicator');
const mobileMenuButton = document.querySelector('.mobile-menu-button');
const sidebarToggle = document.querySelector('.sidebar-toggle');
const suggestionCards = document.querySelectorAll('.suggestion-card');

// LocalStorage anahtarları
const STORAGE_KEY = 'chatHistory';
const ACTIVE_CHAT_KEY = 'activeChatId';

// Global değişkenler
let chatId = localStorage.getItem(ACTIVE_CHAT_KEY) || null;
let chatHistoryData = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};

// Sayfa yükleme işlemleri
document.addEventListener('DOMContentLoaded', () => {
    // DOM elemanlarının varlığını kontrol et
    if (!chatSidebar || !chatContainer || !emptyScreen || !messageContainer || 
        !messageInput || !sendButton || !newChatButton || !chatHistory) {
        console.error('Chat için gerekli DOM elemanları bulunamadı!');
        return; // Gerekli elemanlar yoksa çalışmayı durdur
    }
    
    // LocalStorage'dan sohbet geçmişini yükle
    loadChatHistory();
    
    // Aktif sohbet varsa yükle, yoksa yeni bir sohbet başlat (boş ekran yerine)
    if (chatId && chatHistoryData[chatId]) {
        loadChat(chatId);
    } else {
        // Sayfa ilk yüklendiğinde otomatik olarak yeni sohbet başlat
        createNewChat();
    }
    
    // Textarea yüksekliğini içeriğe göre ayarla
    messageInput.addEventListener('input', autoResizeTextarea);
    
    // Klavye olayları
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e);
        }
    });
    
    // Gönder butonu için event listener
    sendButton.addEventListener('click', (e) => {
        e.preventDefault();
        sendMessage(e);
    });
    
    // Yeni sohbet butonu
    newChatButton.addEventListener('click', (e) => {
        e.preventDefault();
        createNewChat();
    });
    
    // Öneri kartları için event listener
    if (suggestionCards && suggestionCards.length > 0) {
        suggestionCards.forEach(card => {
            card.addEventListener('click', () => {
                const questionText = card.querySelector('p')?.textContent || '';
                if (questionText) {
                    createNewChat(questionText);
                }
            });
        });
    }
    
    // Mobil menü butonu
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', toggleSidebar);
    }
    
    // Sidebar toggle butonu
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Gönder butonunu güncelle
    updateSendButton();
    
    // Mesaj kutusuna odaklan
    if (messageInput) {
        setTimeout(() => messageInput.focus(), 100);
    }
});

// Textarea otomatik yükseklik ayarı
function autoResizeTextarea() {
    if (!messageInput) return;
    
    messageInput.style.height = 'auto';
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 200)}px`;
    updateSendButton();
}

// Gönder butonunu aktif/pasif yapma
function updateSendButton() {
    if (!messageInput || !sendButton) return;
    
    if (messageInput.value.trim() === '') {
        sendButton.disabled = true;
    } else {
        sendButton.disabled = false;
    }
}

// Mesaj gönderme
async function sendMessage(event) {
    if (event) {
        event.preventDefault();
    }
    
    if (!messageInput || !messageContainer) return;
    
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Eğer aktif sohbet yoksa, yeni bir sohbet oluştur
    if (!chatId) {
        chatId = createNewChat(message);
    }
    
    // Kullanıcı mesajını ekle
    addMessageToUI('user', message);
    
    // Mesaj gönderildi, input'u temizle
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateSendButton();
    
    // Sohbet geçmişini güncelle
    updateChatHistory(chatId, 'user', message);
    
    // Yazıyor indikatörünü göster
    showTypingIndicator();
    
    try {
        // API isteği
        const response = await fetch('/process_message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error('API isteği başarısız oldu');
        }
        
        const data = await response.json();
        
        // Yazıyor indikatörünü gizle
        hideTypingIndicator();
        
        // Medya önerisi mi yoksa normal mesaj mı kontrol et
        if (data.isMediaRecommendation) {
            // HTML içeren medya kartlarını ekle
            addHTMLMessageToUI('assistant', data.response);
        } else {
            // Normal metin mesajını ekle
            addMessageToUI('assistant', data.response);
        }
        
        // Sohbet geçmişini güncelle
        updateChatHistory(chatId, 'assistant', data.response);
        
        // Başlığı güncelle (ilk mesaj ise)
        updateChatTitle(chatId);
        
    } catch (error) {
        console.error('Hata:', error);
        hideTypingIndicator();
        addMessageToUI('assistant', 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.');
        updateChatHistory(chatId, 'assistant', 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.');
    }
}

// Mesajı UI'a ekle
function addMessageToUI(role, text) {
    if (!messageContainer || !emptyScreen || !chatContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role === 'user' ? 'user' : ''}`;
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-avatar ${role}">
                ${role === 'user' ? 'S' : 'B'}
            </div>
            <div class="message-text">${text}</div>
        </div>
    `;
    
    messageContainer.appendChild(messageElement);
    
    // Otomatik scroll
    messageContainer.scrollTop = messageContainer.scrollHeight;
    
    // Empty screen'i gizle, chat container'ı göster
    emptyScreen.style.display = 'none';
    chatContainer.style.display = 'flex';
    chatContainer.classList.add('active');
}

// HTML içerikli mesajı UI'a ekle (film/dizi önerileri için)
function addHTMLMessageToUI(role, htmlContent) {
    if (!messageContainer || !emptyScreen || !chatContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role === 'user' ? 'user' : ''}`;
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-avatar ${role}">
                ${role === 'user' ? 'S' : 'B'}
            </div>
            <div class="message-text html-content">${htmlContent}</div>
        </div>
    `;
    
    messageContainer.appendChild(messageElement);
    
    // Otomatik scroll
    messageContainer.scrollTop = messageContainer.scrollHeight;
    
    // Empty screen'i gizle, chat container'ı göster
    emptyScreen.style.display = 'none';
    chatContainer.style.display = 'flex';
    chatContainer.classList.add('active');
}

// Yazıyor indikatörünü göster
function showTypingIndicator() {
    if (!typingIndicator || !messageContainer) return;
    
    typingIndicator.classList.add('active');
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Yazıyor indikatörünü gizle
function hideTypingIndicator() {
    if (!typingIndicator) return;
    
    typingIndicator.classList.remove('active');
}

// Boş ekranı göster
function showEmptyScreen() {
    if (!emptyScreen || !chatContainer) return;
    
    // Artık boş ekranı göstermek yerine hep aktif sohbet alanını göster
    emptyScreen.style.display = 'none';
    chatContainer.style.display = 'flex';
    chatContainer.classList.add('active');
}

// Sohbet geçmişini güncelle
function updateChatHistory(id, role, content) {
    if (!id || !role || !content) return;
    
    if (!chatHistoryData[id]) {
        chatHistoryData[id] = {
            id,
            title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
            createdAt: new Date().toISOString(),
            messages: []
        };
    }
    
    chatHistoryData[id].messages.push({
        role,
        content,
        timestamp: new Date().toISOString()
    });
    
    // LocalStorage'a kaydet
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistoryData));
    localStorage.setItem(ACTIVE_CHAT_KEY, id);
    
    // Sohbet geçmişi listesini güncelle
    renderChatHistoryList();
}

// Sohbet başlığını güncelle (sadece ilk mesaj için)
function updateChatTitle(id) {
    if (!id || !chatHistoryData[id]) return;
    
    const chat = chatHistoryData[id];
    if (chat && chat.messages.length === 2) {
        // İlk kullanıcı mesajından başlık oluştur
        const firstUserMessage = chat.messages[0].content;
        chat.title = firstUserMessage.substring(0, 30) + (firstUserMessage.length > 30 ? '...' : '');
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistoryData));
        renderChatHistoryList();
    }
}

// Sohbet geçmişi listesini oluştur
function renderChatHistoryList() {
    if (!chatHistory) return;
    
    chatHistory.innerHTML = '';
    
    // Tüm sohbetleri silme butonu ekle
    if (Object.keys(chatHistoryData).length > 0) {
        const clearAllButton = document.createElement('div');
        clearAllButton.className = 'clear-all-button';
        clearAllButton.innerHTML = `
            <span>Tüm Sohbetleri Sil</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
        `;
        clearAllButton.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Tüm sohbet geçmişini silmek istediğinize emin misiniz?')) {
                clearAllChats();
            }
        });
        chatHistory.appendChild(clearAllButton);
    }
    
    // Tarih sırasına göre sırala (en yeniden en eskiye)
    const sortedChats = Object.values(chatHistoryData).sort((a, b) => {
        return new Date(b.createdAt) - new Date(a.createdAt);
    });
    
    sortedChats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${chat.id === chatId ? 'active' : ''}`;
        chatItem.dataset.id = chat.id;
        
        chatItem.innerHTML = `
            <div class="chat-item-content">
                <div class="icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <div class="title">${chat.title}</div>
            </div>
            <div class="delete-chat">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </div>
        `;
        
        // Sohbeti yükleme için tıklama olayı
        chatItem.querySelector('.chat-item-content').addEventListener('click', () => loadChat(chat.id));
        
        // Silme butonu için tıklama olayı
        chatItem.querySelector('.delete-chat').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(chat.id);
        });
        
        chatHistory.appendChild(chatItem);
    });
}

// Belirli bir sohbeti sil
function deleteChat(id) {
    if (!id || !chatHistoryData[id]) return;
    
    // Chatbot'un onayını al
    if (confirm('Bu sohbeti silmek istediğinize emin misiniz?')) {
        // Eğer aktif sohbet siliniyorsa
        if (id === chatId) {
            // Sohbeti temizle ve yeni bir boş ekran göster
            showEmptyScreen();
            chatId = null;
            localStorage.removeItem(ACTIVE_CHAT_KEY);
        }
        
        // Sohbeti sil
        delete chatHistoryData[id];
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistoryData));
        
        // Listeyi güncelle
        renderChatHistoryList();
    }
}

// Tüm sohbetleri sil
function clearAllChats() {
    // LocalStorage'dan tüm sohbet verilerini temizle
    chatHistoryData = {};
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(ACTIVE_CHAT_KEY);
    
    // Aktif sohbeti sıfırla
    chatId = null;
    
    // Boş ekranı göster
    showEmptyScreen();
    
    // Sohbet listesini güncelle
    renderChatHistoryList();
}

// Yeni sohbet oluştur
function createNewChat(initialMessage = null) {
    if (!messageContainer || !chatContainer || !emptyScreen) return null;
    
    // Yeni bir ID oluştur
    const newChatId = 'chat_' + Date.now();
    chatId = newChatId;
    
    // Aktif sohbet ID'sini güncelle
    localStorage.setItem(ACTIVE_CHAT_KEY, newChatId);
    
    // UI'ı temizle
    messageContainer.innerHTML = '';
    
    // Boş ekranı gizle, chat container'ı göster
    emptyScreen.style.display = 'none';
    chatContainer.style.display = 'flex';
    chatContainer.classList.add('active');
    
    // Sohbet listesini güncelle
    renderChatHistoryList();
    
    // Eğer başlangıç mesajı varsa, otomatik olarak gönder
    if (initialMessage && messageInput) {
        messageInput.value = initialMessage;
        setTimeout(() => sendMessage(), 100);
    } else if (messageInput) {
        // Mesaj inputuna odaklan
        setTimeout(() => messageInput.focus(), 100);
    }
    
    // Mobilde sidebar'ı kapat
    if (window.innerWidth <= 768 && chatSidebar) {
        chatSidebar.classList.remove('active');
    }
    
    return newChatId;
}

// Belirli bir sohbeti yükle
function loadChat(id) {
    if (!id || !chatHistoryData[id] || !messageContainer) return;
    
    chatId = id;
    localStorage.setItem(ACTIVE_CHAT_KEY, id);
    
    // UI'ı temizle
    messageContainer.innerHTML = '';
    
    // Tüm mesajları ekle
    chatHistoryData[id].messages.forEach(msg => {
        addMessageToUI(msg.role, msg.content);
    });
    
    // Sohbet listesini güncelle (active class'ı için)
    renderChatHistoryList();
    
    // Mobilde sidebar'ı kapat
    if (window.innerWidth <= 768 && chatSidebar) {
        chatSidebar.classList.remove('active');
    }
}

// LocalStorage'dan sohbet geçmişini yükle
function loadChatHistory() {
    chatHistoryData = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    renderChatHistoryList();
}

// Sidebar aç/kapa
function toggleSidebar() {
    if (!chatSidebar) return;
    
    chatSidebar.classList.toggle('active');
}

// CSRF token alma
function getCsrfToken() {
    const csrfCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    return '';
}