import requests
import json
import os
from datetime import datetime

# ==========================================
# CONFIG - URLs Oficiais NY Data
# ==========================================
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=1000&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=1000&$order=draw_date DESC"

HEADERS = {'User-Agent': 'LotoLab-Pro/2.0'}

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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

                # 1. NÚMEROS BRANCOS (whites)
                winning_numbers = item.get("winning_numbers", "")
                if not winning_numbers: continue
                
                # Na API de NY, winning_numbers contém apenas as 5 bolas brancas
                whites = [int(n) for n in winning_numbers.split()]

                # 2. BOLA ESPECIAL (s)
                # Powerball usa campo 'powerball', Mega Millions usa 'mega_ball'
                if game_type == "pb":
                    special = int(item.get("powerball", 0))
                else:
                    special = int(item.get("mega_ball", 0))

                # 3. MULTIPLICADOR (m)
                if game_type == "pb":
                    m_raw = str(item.get("power_play", "1"))
                else:
                    m_raw = str(item.get("multiplier", "1"))
                
                # Limpeza de texto (remove 'x', espaços e garante ser dígito)
                m_clean = m_raw.lower().replace("x", "").strip()
                multiplier = int(m_clean) if m_clean.isdigit() else 1

                seen_dates.add(draw_date)
                processed.append({
                    "d": draw_date,
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                })

            except Exception:
                continue

        # Ordenação garantida por data decrescente
        processed.sort(key=lambda x: x["d"], reverse=True)

        if not processed:
            print(f"⚠️ Nenhum dado válido {game_type}")
            return

        # Gerar arquivos (Recent: 10 com Payout | History: Todos)
        recent = [dict(item, p=format_payouts(game_type)) for item in processed[:10]]

        save_json(f"{game_type}_history.json", processed)
        save_json(f"{game_type}_recent.json", recent)

        print(f"✅ {game_type.upper()} OK | {len(processed)} concursos | Último: {processed[0]['d']}")

    except Exception as e:
        print(f"💥 Erro fatal {game_type}: {e}")

if __name__ == "__main__":
    print("\n==============================")
    print("🎰 LOTOLAB DATA ENGINE v2")
    print("==============================")
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
    
    # Salva timestamp do update
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    print("\n🚀 Pronto! Verifique os arquivos JSON no repositório.")
