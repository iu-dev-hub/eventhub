#!/usr/bin/env bash
# ========================================================
# AURA Events - Android & Yönetici Portalı Çalıştırma Betiği
# ========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONDA_ENV="/home/berkyilmaz/anaconda3/envs/flet"
PYTHON_BIN="$CONDA_ENV/bin/python"
FLET_BIN="$CONDA_ENV/bin/flet"

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

echo "=========================================================="
echo "📱 AURA Events - Kültür & Sahne Sanatları Portalı"
echo "=========================================================="
echo "Komutlar:"
echo "  ./run_android.sh            -> Kullanıcı Mobil Uygulaması (Android Form)"
echo "  ./run_android.sh admin      -> Ayrı Yönetici Paneli & Canlı API İstasyonu"
echo "  ./run_android.sh live       -> Android Telefonlar İçin Yerel Ağda Yayınla (Port 8550)"
echo "  ./run_android.sh apk        -> Bağımsız Android APK Derle"
echo "=========================================================="
echo "🌐 Bilgisayar Yerel IP: $LOCAL_IP"
echo "📲 Android telefondan canlı bağlantı adresi: http://$LOCAL_IP:8550"
echo "=========================================================="

case "$1" in
    "admin")
        echo "⚙️ Ayrı Yönetici Paneli & API Kontrol Merkezi Açılıyor..."
        exec "$PYTHON_BIN" src/main.py --admin
        ;;
    "live"|"web"|"android-live")
        echo "🚀 Android Canlı Ağı Başlatılıyor (0.0.0.0:8550)..."
        exec "$FLET_BIN" run --port 8550 --host 0.0.0.0 --web main.py
        ;;
    "apk")
        echo "📦 Android APK Derlemesi Başlatılıyor..."
        exec "$FLET_BIN" build apk --project "AURA" --org "com.aura.events"
        ;;
    *)
        echo "📱 Kullanıcı Mobil Deneyimi Başlatılıyor..."
        exec "$PYTHON_BIN" main.py
        ;;
esac
