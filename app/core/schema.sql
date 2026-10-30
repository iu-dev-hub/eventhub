-- EventHub: database schema
--
-- Bu dosya Sprint 2'de ekipler tarafından doldurulacaktır.
--
-- Kurallar:
--   - Her ekip kendi tablolarını yazar; tabloların sahibi yorum satırında belirtilir.
--   - Tablo ve sütun adları İngilizce, snake_case; tablo adları çoğul (ör. tickets).
--   - Başka ekibin tablosuna referans (FOREIGN KEY) veren tablolar, o ekiple
--     Scrum of Scrums'ta konuşularak tasarlanır ve docs/interface-contract.md'ye yazılır.
--   - Bu dosya app/core/ altında olduğu için değişiklikler Scrum Master'ların onayını gerektirir.
--
-- Örnek biçim:
--
--   -- Owner: team-events
--   DROP TABLE IF EXISTS venues;
--   CREATE TABLE venues (
--       id        INTEGER PRIMARY KEY AUTOINCREMENT,
--       name      TEXT    NOT NULL UNIQUE,
--       capacity  INTEGER NOT NULL CHECK (capacity > 0)
--   );

-- Owner: team-events
-- BR-2.1: Her salonun adı, adresi ve kapasitesi vardır (salonları yalnızca yöneticiler tanımlar).
CREATE TABLE IF NOT EXISTS venues (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL UNIQUE,
    address   TEXT    NOT NULL,
    capacity  INTEGER NOT NULL CHECK (capacity > 0)
);

-- Owner: team-tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'reserved', -- reserved (beklemede), paid (aktif/ödendi), cancelled (iptal)
    qr_code TEXT UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
-- Owner: team-accounts
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'participant',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Owner: team-events
-- TG-117 / PB-08: Etkinlikler. Yeni etkinlikler 'draft' olarak kaydedilir;
-- organizer_id -> users.id (Accounts onaylı); tickets.event_id -> events.id
-- (Tickets onaylı, FOREIGN KEY tickets tablosunda tanımlıdır).
-- Servis katmanı: draft etkinliklerde bilet oluşturma/rezervasyon/satış engellenir.
-- BR-1.5 (organizatör yönetici onayı) TG-118 kapsamında ayrıca uygulanacaktır;
-- onay mekanizması bitene kadar taslak oluşturma yalnızca rol kontrolüne bırakılmamalıdır.
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    venue_id     INTEGER NOT NULL,
    start_time   TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    price        REAL    NOT NULL DEFAULT 0 CHECK (price >= 0),
    status       TEXT    NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    organizer_id INTEGER NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (organizer_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_events_organizer_id ON events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);

