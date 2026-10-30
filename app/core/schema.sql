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
    created_at TEXT NOT NULL
);
-- Owner: team-accounts
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name     TEXT    NOT NULL DEFAULT '',
    last_name      TEXT    NOT NULL DEFAULT '',
    email          TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    role           TEXT    NOT NULL DEFAULT 'participant',
    is_student     BOOLEAN NOT NULL DEFAULT 0,
    student_number TEXT    DEFAULT NULL,
    notify_email   BOOLEAN NOT NULL DEFAULT 1,
    avatar_url     TEXT    DEFAULT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    token_hash TEXT    NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used       BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

