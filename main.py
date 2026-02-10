import requests
import json
from datetime import datetime

# URLs OFICIAIS ATUALIZADAS (Portal de Dados de NY)
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=1000&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=1000&$order=draw_date DESC"

HEADERS = {'User-Agent': 'LotoLab-Pro/2.0'}

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_game(url, game_type):
    print(f"\n📡 Lendo {game_type.upper()}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erro {game_type}: {response.status_code}")
            return

        raw_data = response.json()
        processed = []
        seen_dates = set()

        for item in raw_data:
            try:
                date = item.get("draw_date", "").split("T")[0]
                if not date or date in seen_dates: continue

                # Extração Inteligente de Números
                raw_nums = item.get("winning_numbers", "").split()
                if not raw_nums: continue

                # Identificar Bola Especial (Powerball/Mega Ball)
                # Às vezes vem na string 'winning_numbers', às vezes em campo separado
                if len(raw_nums) >= 6:
                    whites = [int(n) for n in raw_nums[:5]]
                    special = int(raw_nums[5])
                else:
                    whites = [int(n) for n in raw_nums]
                    # Busca campo secundário se a string principal estiver curta
                    special = int(item.get("powerball") or item.get("mega_ball") or 0)

                # Multiplicador
                m_val = str(item.get("power_play") or item.get("multiplier") or "1")
                multiplier = int(m_val.lower().replace("x", "").strip())

                processed.append({
                    "d": date,
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                })
                seen_dates.add(date)

            except: continue

        # Salvar Arquivos
        if processed:
            processed.sort(key=lambda x: x["d"], reverse=True)
            # Recent (10 com Payout)
            recent = [dict(item, p=format_payouts(game_type)) for item in processed[:10]]
            
            with open(f"{game_type}_history.json", "w") as f:
                json.dump(processed, f, indent=2)
            with open(f"{game_type}_recent.json", "w") as f:
                json.dump(recent, f, indent=2)
            
            print(f"✅ {game_type.upper()} OK: {len(processed)} registros.")

    except Exception as e:
        print(f"💥 Falha fatal {game_type}: {e}")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
