import requests
import json
import os
from datetime import datetime

# URLs OFICIAIS ATUALIZADAS (NY Open Data)
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=1000&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=1000&$order=draw_date DESC"

HEADERS = {'User-Agent': 'LotoLab-Pro/2.0'}

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_game(url, game_type):
    print(f"\n📡 Conectando ao servidor: {game_type.upper()}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erro na API {game_type}: {response.status_code}")
            return

        raw_data = response.json()
        processed = []
        seen_dates = set()

        for item in raw_data:
            try:
                draw_date = item.get("draw_date", "").split("T")[0]
                if not draw_date or draw_date in seen_dates: continue

                # Captura números brancos
                win_nums = item.get("winning_numbers", "")
                if not win_nums: continue
                whites = [int(n) for n in win_nums.split()]

                # Captura bola especial (Lógica diferente para cada jogo)
                if game_type == "pb":
                    special = int(item.get("powerball", 0))
                    m_raw = str(item.get("power_play", "1"))
                else:
                    special = int(item.get("mega_ball", 0))
                    m_raw = str(item.get("multiplier", "1"))

                # Limpeza do multiplicador
                m_clean = m_raw.lower().replace("x", "").strip()
                multiplier = int(m_clean) if m_clean.isdigit() else 1

                processed.append({
                    "d": draw_date,
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                })
                seen_dates.add(draw_date)
            except: continue

        if processed:
            processed.sort(key=lambda x: x["d"], reverse=True)
            # Salva Histórico Completo
            with open(f"{game_type}_history.json", "w", encoding="utf-8") as f:
                json.dump(processed, f, indent=2)
            # Salva Recentes (10 com prêmios)
            recent = [dict(item, p=format_payouts(game_type)) for item in processed[:10]]
            with open(f"{game_type}_recent.json", "w", encoding="utf-8") as f:
                json.dump(recent, f, indent=2)
            print(f"✅ {game_type.upper()} OK: {len(processed)} sorteios processados.")
    except Exception as e:
        print(f"💥 Erro fatal em {game_type}: {e}")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
