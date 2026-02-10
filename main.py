import requests
import json
import os
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=1000&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=1000&$order=draw_date DESC"

HEADERS = {'User-Agent': 'LotoLab-Pro/2.0'}

# ==========================================
# PAYOUTS PADRÃO
# ==========================================
def format_payouts(game_type):
    if game_type == "pb":
        return {
            "5+1": "Jackpot",
            "5+0": "$1M",
            "4+1": "$50k",
            "4+0": "$100"
        }
    else:
        return {
            "5+1": "Jackpot",
            "5+0": "$1M",
            "4+1": "$10k",
            "4+0": "$500"
        }

# ==========================================
# SALVAR JSON SEGURO
# ==========================================
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ==========================================
# PROCESSADOR PRINCIPAL
# ==========================================
def process_game(url, game_type):
    print(f"\n📡 Baixando {game_type.upper()} ...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            print(f"❌ Erro API {game_type}: {response.status_code}")
            return

        raw_data = response.json()
        processed = []
        seen_dates = set()

        for item in raw_data:
            try:
                draw_date = item.get("draw_date", "").split("T")[0]
                if not draw_date or draw_date in seen_dates:
                    continue

                seen_dates.add(draw_date)

                # ---------------------------
                # NUMEROS PRINCIPAIS
                # ---------------------------
                winning_numbers = item.get("winning_numbers", "")
                if not winning_numbers:
                    continue

                whites = [int(n) for n in winning_numbers.split()]

                # ---------------------------
                # BOLA ESPECIAL
                # ---------------------------
                if game_type == "pb":
                    special = int(item.get("powerball", 0))
                else:
                    special = int(item.get("mega_ball", 0))

                # ---------------------------
                # MULTIPLICADOR
                # ---------------------------
                if game_type == "pb":
                    m_raw = str(item.get("power_play", "1")).lower().replace("x", "").strip()
                else:
                    m_raw = str(item.get("multiplier", "1")).lower().replace("x", "").strip()

                multiplier = int(m_raw) if m_raw.isdigit() else 1

                processed.append({
                    "d": draw_date,
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                })

            except Exception:
                continue

        # ----------------------------------
        # ORDENA POR DATA
        # ----------------------------------
        processed.sort(key=lambda x: x["d"], reverse=True)

        if not processed:
            print(f"⚠️ Nenhum dado válido {game_type}")
            return

        # ----------------------------------
        # RECENTES COM PAYOUT
        # ----------------------------------
        recent = [
            dict(item, p=format_payouts(game_type))
            for item in processed[:10]
        ]

        # ----------------------------------
        # SALVAR
        # ----------------------------------
        save_json(f"{game_type}_history.json", processed)
        save_json(f"{game_type}_recent.json", recent)

        print(f"✅ {game_type.upper()} OK")
        print(f"   concursos: {len(processed)}")
        print(f"   ultimo: {processed[0]['d']}")

    except Exception as e:
        print(f"💥 Erro fatal {game_type}: {e}")

# ==========================================
# AUTO UPDATE DIÁRIO
# ==========================================
def save_last_update():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("last_update.txt", "w") as f:
        f.write(now)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print("\n==============================")
    print("🎰 LOTOLAB DATA ENGINE v2")
    print("==============================")

    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")

    save_last_update()

    print("\n📁 Arquivos gerados:")
    print("pb_history.json")
    print("pb_recent.json")
    print("mm_history.json")
    print("mm_recent.json")
    print("\n🚀 Pronto para IA / App / API")
