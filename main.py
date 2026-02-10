import requests
import json

# URLs Oficiais (Socrata API)
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=100&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=100&$order=draw_date DESC"

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_game(url, game_type):
    print(f"Processando {game_type}...")
    try:
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            print(f"Erro na API {game_type}: {response.status_code}")
            return
        
        raw_data = response.json()
        processed_list = []

        for item in raw_data:
            try:
                # Extração segura dos números
                winning_numbers = item.get('winning_numbers', '')
                if not winning_numbers: continue
                
                parts = winning_numbers.split()
                
                # Para Powerball e Mega Millions padrão (5 brancas + 1 especial)
                if len(parts) >= 6:
                    whites = [int(n) for n in parts[:5]]
                    special = int(parts[5])
                else:
                    # Fallback para Mega Millions caso a Mega Ball esteja em outro campo
                    whites = [int(n) for n in parts]
                    special = int(item.get('mega_ball', 0))

                # Limpeza do Multiplicador (Ex: "3" ou "3x" vira 3)
                mult_raw = str(item.get('multiplier', '1')).lower().replace('x', '').strip()
                multiplier = int(float(mult_raw)) if mult_raw and mult_raw != 'none' else 1

                obj = {
                    "d": item.get('draw_date', '').split('T')[0],
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                }
                processed_list.append(obj)
            except:
                continue # Pula sorteios com erro de formatação

        # --- SALVAR ARQUIVOS ---
        # 1. Recentes (10 com Payouts)
        recent = []
        for item in processed_list[:10]:
            temp = item.copy()
            temp["p"] = format_payouts(game_type)
            recent.append(temp)
        
        with open(f'{game_type}_recent.json', 'w') as f:
            json.dump(recent, f, indent=2)

        # 2. Histórico (Sem Payouts)
        with open(f'{game_type}_history.json', 'w') as f:
            json.dump(processed_list, f, indent=2)
            
        print(f"Sucesso: Arquivos de {game_type} criados.")

    except Exception as e:
        print(f"Erro fatal no processamento de {game_type}: {e}")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
