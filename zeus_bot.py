import os
import re

# ============================================================
# AYARLAR
# ============================================================

FOLDER = "teyzeniyerim1"

# ============================================================
# M3U8 DOSYALARINI GÜNCELLE
# ============================================================

def update_m3u8_files():
    if not os.path.isdir(FOLDER):
        print(f"❌ Klasör bulunamadı: {FOLDER}")
        return

    print(f"📁 Klasör: {FOLDER}")
    print("🔍 .m3u8 dosyaları taranıyor...\n")

    total = 0
    changed = 0

    for filename in os.listdir(FOLDER):

        # Sadece .m3u8 dosyalarına dokun
        if not filename.lower().endswith(".m3u8"):
            continue

        filepath = os.path.join(FOLDER, filename)
        total += 1

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Sadece URL sonundaki /index.m3u8 kısmını
            # /index.txt olarak değiştir.
            new_content = re.sub(
                r'/index\.m3u8(?=\s*$)',
                '/index.txt',
                content,
                flags=re.MULTILINE
            )

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

                changed += 1
                print(f"✅ Güncellendi: {filename}")
            else:
                print(f"⏭️ Değişiklik yok: {filename}")

        except Exception as e:
            print(f"❌ Hata: {filename} -> {e}")

    print("\n" + "=" * 50)
    print(f"📊 Toplam .m3u8 dosyası : {total}")
    print(f"✏️ Değiştirilen dosya   : {changed}")
    print(f"⏭️ Değişmeyen dosya     : {total - changed}")
    print("=" * 50)
    print("\n🎉 İşlem tamamlandı!")


# ============================================================
# BAŞLAT
# ============================================================

if __name__ == "__main__":
    update_m3u8_files()
