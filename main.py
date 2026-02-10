import requests
import json

# URLs ATUALIZADAS E TESTADAS (Socrata API)
# Powerball: https://data.ny.gov/Government/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-mqv8
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=100&$order=draw_date DESC"

# Mega Millions: https://data.ny.gov/Government/Lottery-Mega-Millions-Winning-Numbers-Beginning-20/5xaw-6ayf
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=100&$order=draw_date DESC"

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_game(url, game_type):
    print(f"Processando {game_type}...")
    try:
        # User-agent para evitar ser bloqueado pelo servidor do governo
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"Erro na API {game_type}: {response.status_code}")
            return
        
        raw_data = response.json()
        processed_list = []

        for item in raw_data:
            try:
                # Pegar números (A Powerball as vezes usa campos diferentes)
                winning_numbers = item.get('winning_numbers', '')
                if not winning_numbers: continue
                
                parts = winning_numbers.split()
                
                # Para Powerball e Mega Millions padrão (5 brancas + 1 especial)
                if len(parts) >= 6:
                    whites = [int(n) for n in parts[:5]]
                    special = int(parts[5])
                else:
                    # Se vier menos de 6, tenta o campo da Mega Ball
                    whites = [int(n) for n in parts]
                    special = int(item.get('mega_ball', 0))

                # Multiplicador (Limpeza total)
                mult_raw = str(item.get('multiplier', '1')).lower().replace('x', '').strip()
                try:
                    multiplier = int(float(mult_raw))
                except:
                    multiplier = 1

                obj = {
                    "d": item.get('draw_date', '').split('T')[0],
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                }
                processed_list.append(obj)
            except:
                continue 

        # --- SALVAR ARQUIVOS ---
        recent = []
        for item in processed_list[:10]:
            temp = item.copy()
            temp["p"] = format_payouts(game_type)
            recent.append(temp)
        
        with open(f'{game_type}_recent.json', 'w') as f:
            json.dump(recent, f, indent=2)

        with open(f'{game_type}_history.json', 'w') as f:
            json.dump(processed_list, f, indent=2)
            
        print(f"Sucesso: Arquivos de {game_type} criados.")

    except Exception as e:
        print(f"Erro fatal no processamento de {game_type}: {e}")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
