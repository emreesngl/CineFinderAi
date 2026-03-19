-- Supabase PostgreSQL Schema for Django Film Projesi
-- Bu dosya tüm Django modellerini PostgreSQL formatında içerir

-- Auth Users tablosu (Django AbstractUser'dan)
CREATE TABLE auth_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bio TEXT,
    profile_picture VARCHAR(255),  -- ImageField için file path
    points INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    CHECK (points >= 0),
    CHECK (level >= 1)
);

-- Badge (Rozet) tablosu
CREATE TABLE core_badge (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    icon VARCHAR(255),  -- ImageField için file path
    category VARCHAR(50) NOT NULL DEFAULT 'special',
    tier VARCHAR(10) NOT NULL DEFAULT 'bronze',
    tier_order INTEGER NOT NULL DEFAULT 1,
    points_required INTEGER,
    comment_count_required INTEGER,
    favorites_count_required INTEGER,
    ratings_count_required INTEGER,
    followers_count_required INTEGER,
    following_count_required INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (category IN ('rating', 'commenting', 'collection', 'social', 'community', 'special')),
    CHECK (tier IN ('bronze', 'silver', 'gold')),
    CHECK (tier_order >= 1)
);

-- User-Badge Many-to-Many relationship tablosu
CREATE TABLE auth_user_badges (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    badge_id BIGINT NOT NULL REFERENCES core_badge(id) ON DELETE CASCADE,
    UNIQUE(user_id, badge_id)
);

-- Media (Film/Dizi) tablosu
CREATE TABLE core_media (
    id BIGSERIAL PRIMARY KEY,
    tmdb_id VARCHAR(20) NOT NULL,
    media_type VARCHAR(5) NOT NULL,
    title VARCHAR(255),
    poster_path VARCHAR(255),
    UNIQUE(tmdb_id, media_type),
    CHECK (media_type IN ('movie', 'tv'))
);

-- UserList (Favoriler, İzlenecekler vb.) tablosu
CREATE TABLE core_userlist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    media_id BIGINT NOT NULL REFERENCES core_media(id) ON DELETE CASCADE,
    list_type VARCHAR(10) NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, media_id, list_type),
    CHECK (list_type IN ('favorite', 'watchlist', 'follow'))
);

-- Comment (Yorum) tablosu
CREATE TABLE core_comment (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    media_id BIGINT NOT NULL REFERENCES core_media(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rating (Puanlama) tablosu
CREATE TABLE core_rating (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    media_id BIGINT NOT NULL REFERENCES core_media(id) ON DELETE CASCADE,
    score SMALLINT NOT NULL,
    rated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, media_id),
    CHECK (score >= 1 AND score <= 10)
);

-- Follow (Takip) tablosu
CREATE TABLE core_follow (
    id BIGSERIAL PRIMARY KEY,
    follower_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    followed_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(follower_id, followed_id),
    CHECK (follower_id != followed_id)
);

-- Message (Mesaj) tablosu
CREATE TABLE core_message (
    id BIGSERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    receiver_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE
);

-- Notification (Bildirim) tablosu
CREATE TABLE core_notification (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    media_id BIGINT REFERENCES core_media(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    link VARCHAR(200)
);

-- ChatConversation (Sohbet Konuşması) tablosu
CREATE TABLE core_chatconversation (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'Yeni Sohbet',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ChatMessage (Sohbet Mesajı) tablosu
CREATE TABLE core_chatmessage (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES core_chatconversation(id) ON DELETE CASCADE,
    sender_is_user BOOLEAN NOT NULL DEFAULT TRUE,
    text TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    recommendations_json JSONB
);

-- UserHiddenConversation (Gizlenen Sohbet) tablosu
CREATE TABLE core_userhiddenconversation (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    other_user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    hidden_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, other_user_id)
);

-- Django Groups ve Permissions (Django admin için gerekli)
CREATE TABLE auth_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_permission (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id INTEGER NOT NULL,
    codename VARCHAR(100) NOT NULL
);

CREATE TABLE django_content_type (
    id SERIAL PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE(app_label, model)
);

CREATE TABLE auth_user_groups (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE(user_id, group_id)
);

CREATE TABLE auth_user_user_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE(user_id, permission_id)
);

CREATE TABLE auth_group_permissions (
    id BIGSERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE(group_id, permission_id)
);

-- Django Sessions (oturum yönetimi için)
CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMPTZ NOT NULL
);

-- Django Migrations (migration takibi için)
CREATE TABLE django_migrations (
    id BIGSERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMPTZ NOT NULL
);

-- Django Admin Log (admin paneli için)
CREATE TABLE django_admin_log (
    id SERIAL PRIMARY KEY,
    action_time TIMESTAMPTZ NOT NULL,
    object_id TEXT,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT NOT NULL,
    change_message TEXT NOT NULL,
    content_type_id INTEGER REFERENCES django_content_type(id) ON DELETE SET NULL,
    user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    CHECK (action_flag >= 0)
);

-- İndeksler (Performans için)
CREATE INDEX idx_auth_user_username ON auth_user(username);
CREATE INDEX idx_auth_user_email ON auth_user(email);
CREATE INDEX idx_core_media_tmdb_id ON core_media(tmdb_id);
CREATE INDEX idx_core_media_media_type ON core_media(media_type);
CREATE INDEX idx_core_userlist_user_id ON core_userlist(user_id);
CREATE INDEX idx_core_userlist_media_id ON core_userlist(media_id);
CREATE INDEX idx_core_userlist_list_type ON core_userlist(list_type);
CREATE INDEX idx_core_comment_user_id ON core_comment(user_id);
CREATE INDEX idx_core_comment_media_id ON core_comment(media_id);
CREATE INDEX idx_core_comment_created_at ON core_comment(created_at);
CREATE INDEX idx_core_rating_user_id ON core_rating(user_id);
CREATE INDEX idx_core_rating_media_id ON core_rating(media_id);
CREATE INDEX idx_core_follow_follower_id ON core_follow(follower_id);
CREATE INDEX idx_core_follow_followed_id ON core_follow(followed_id);
CREATE INDEX idx_core_message_sender_id ON core_message(sender_id);
CREATE INDEX idx_core_message_receiver_id ON core_message(receiver_id);
CREATE INDEX idx_core_message_sent_at ON core_message(sent_at);
CREATE INDEX idx_core_notification_user_id ON core_notification(user_id);
CREATE INDEX idx_core_notification_is_read ON core_notification(is_read);
CREATE INDEX idx_core_chatconversation_user_id ON core_chatconversation(user_id);
CREATE INDEX idx_core_chatconversation_updated_at ON core_chatconversation(updated_at);
CREATE INDEX idx_core_chatmessage_conversation_id ON core_chatmessage(conversation_id);
CREATE INDEX idx_core_chatmessage_sent_at ON core_chatmessage(sent_at);
CREATE INDEX idx_badge_category ON core_badge(category);
CREATE INDEX idx_badge_tier ON core_badge(tier);
CREATE INDEX idx_badge_is_active ON core_badge(is_active);

-- Triggers (auto-updated_at için)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_core_comment_updated_at 
    BEFORE UPDATE ON core_comment 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_core_chatconversation_updated_at 
    BEFORE UPDATE ON core_chatconversation 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Foreign Key Constraints eklemeleri
ALTER TABLE auth_permission ADD CONSTRAINT auth_permission_content_type_id_fkey 
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) ON DELETE CASCADE;

-- RLS (Row Level Security) politikaları (Supabase için önemli)
ALTER TABLE auth_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_badge ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_userlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_comment ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_rating ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_follow ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_message ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_notification ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_chatconversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_chatmessage ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_userhiddenconversation ENABLE ROW LEVEL SECURITY;

-- Temel RLS politikaları (kullanıcı sadece kendi verilerine erişebilir)
CREATE POLICY "Users can view own profile" ON auth_user FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "Users can update own profile" ON auth_user FOR UPDATE USING (auth.uid()::text = id::text);

-- Badges herkes görebilir
CREATE POLICY "Badges are viewable by everyone" ON core_badge FOR SELECT USING (is_active = true);

-- Media herkes görebilir
CREATE POLICY "Media is viewable by everyone" ON core_media FOR SELECT USING (true);

-- UserList politikaları
CREATE POLICY "Users can manage own lists" ON core_userlist FOR ALL USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can view others' public lists" ON core_userlist FOR SELECT USING (true);

-- Comment politikaları
CREATE POLICY "Users can manage own comments" ON core_comment FOR ALL USING (auth.uid()::text = user_id::text);
CREATE POLICY "Comments are viewable by everyone" ON core_comment FOR SELECT USING (true);

-- Rating politikaları
CREATE POLICY "Users can manage own ratings" ON core_rating FOR ALL USING (auth.uid()::text = user_id::text);
CREATE POLICY "Ratings are viewable by everyone" ON core_rating FOR SELECT USING (true);

-- Follow politikaları
CREATE POLICY "Users can manage own follows" ON core_follow FOR ALL USING (auth.uid()::text = follower_id::text);
CREATE POLICY "Follows are viewable by everyone" ON core_follow FOR SELECT USING (true);

-- Message politikaları
CREATE POLICY "Users can view own messages" ON core_message FOR SELECT USING (
    auth.uid()::text = sender_id::text OR auth.uid()::text = receiver_id::text
);
CREATE POLICY "Users can send messages" ON core_message FOR INSERT WITH CHECK (auth.uid()::text = sender_id::text);
CREATE POLICY "Users can update own sent messages" ON core_message FOR UPDATE USING (auth.uid()::text = sender_id::text);

-- Notification politikaları
CREATE POLICY "Users can view own notifications" ON core_notification FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can update own notifications" ON core_notification FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Chat politikaları
CREATE POLICY "Users can manage own chat conversations" ON core_chatconversation FOR ALL USING (auth.uid()::text = user_id::text);
CREATE POLICY "Users can manage own chat messages" ON core_chatmessage FOR ALL USING (
    EXISTS (SELECT 1 FROM core_chatconversation WHERE id = conversation_id AND auth.uid()::text = user_id::text)
);

-- Hidden conversation politikaları
CREATE POLICY "Users can manage own hidden conversations" ON core_userhiddenconversation FOR ALL USING (auth.uid()::text = user_id::text);

-- Dummy data eklemeleri (isteğe bağlı)
-- INSERT INTO django_content_type (app_label, model) VALUES 
-- ('core', 'user'), ('core', 'media'), ('core', 'badge'), ('core', 'userlist'), 
-- ('core', 'comment'), ('core', 'rating'), ('core', 'follow'), ('core', 'message'),
-- ('core', 'notification'), ('core', 'chatconversation'), ('core', 'chatmessage'); 