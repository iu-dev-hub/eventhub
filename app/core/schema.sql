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
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'participant',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

