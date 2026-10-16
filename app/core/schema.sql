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

