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
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'participant',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- Owner: team-payments
-- Koltuklar: etkinlik başına koltuk kodu benzersizdir.
-- event_id için FOREIGN KEY şimdilik yok: events tablosu henüz şemada tanımlı değil.
-- team-events tabloyu ekleyince interface-contract.md'ye yazılıp FK eklenecek.
CREATE TABLE IF NOT EXISTS seats (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     INTEGER NOT NULL,
    seat_code    TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'available'
                 CHECK (status IN ('available', 'locked', 'sold')),
    locked_until TEXT,
    UNIQUE (event_id, seat_code)
);

-- Owner: team-payments
-- Ödeme denemeleri: başarılı ve başarısız hepsi tutulur (eski payment_logs yerine).
-- Kartın tamamı ASLA saklanmaz, yalnızca son 4 hane.
CREATE TABLE IF NOT EXISTS payments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amount     REAL,
    card_last4 TEXT,
    success    INTEGER NOT NULL CHECK (success IN (0, 1)),
    message    TEXT    NOT NULL,
    seats      TEXT    NOT NULL,  -- JSON metin: ["A1","A2"]
    created_at TEXT    NOT NULL
);