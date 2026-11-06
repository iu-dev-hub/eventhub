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
-- NOT: Eskiden burada DROP TABLE IF EXISTS users vardı. events.organizer_id -> users.id
-- FK'si eklendiği için (PRAGMA foreign_keys = ON) init-db tekrar çalıştığında events
-- kayıtları varken bu DROP FOREIGN KEY hatası veriyordu; diğer tablolar gibi IF NOT EXISTS yapıldı.
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

-- Owner: team-events
-- TG-117 / PB-08: Etkinlikler. Yeni etkinlikler 'draft' olarak kaydedilir;
-- organizer_id -> users.id: Product Owner kararı ve Team Accounts yanıtıyla uyumlu.
-- tickets.event_id -> events.id: Team Tickets ve Team Accounts tarafından teyit edildi.
-- Draft kuralı: draft (published olmayan) etkinliklerde bilet satışı yapılmaz. Team Tickets
-- bu kontrolü kendi purchase_ticket servisine ekliyor (servis katmanı; bu dosyanın kapsamı dışı).
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

-- Owner: team-payments
-- Rezervasyonlar: başarılı ödemelerle ilişkili rezervasyon kaydı.
-- idempotency_key benzersizdir (mükerrer ödeme/istek engelleme).
CREATE TABLE IF NOT EXISTS reservations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id      INTEGER NOT NULL,
    event_id        INTEGER NOT NULL,
    user_id         INTEGER,
    idempotency_key TEXT UNIQUE,
    ticket_code     TEXT UNIQUE,
    status          TEXT NOT NULL DEFAULT 'confirmed'
                    CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    created_at      TEXT NOT NULL,
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);

-- Owner: team-payments
-- Rezervasyon-Koltuk ilişkisi: etkinlikte bir koltuk aynı anda yalnızca tek bir rezervasyonda bulunabilir.
CREATE TABLE IF NOT EXISTS reservation_seats (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    event_id       INTEGER NOT NULL,
    seat_code      TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
    UNIQUE (event_id, seat_code)
);
