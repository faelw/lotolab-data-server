import requests
import json

# NOVAS URLs OFICIAIS (TESTADAS)
# Powerball: dataset d6yy-mqv8
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=100&$order=draw_date DESC"
# Mega Millions: dataset 5xaw-6ayf
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=100&$order=draw_date DESC"

def format_payouts(game_type):
    """Padrão de rateio LotoLab"""
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_game(url, game_type):
    print(f"Lendo dados de {game_type.upper()}...")
    try:
        # Headers para evitar bloqueio de robôs
        headers = {'User-Agent': 'LotoLab-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"Erro na API {game_type}: {response.status_code}")
            return
        
        raw_data = response.json()
        processed_list = []

        for item in raw_data:
            try:
                draw_date = item.get('draw_date', '').split('T')[0]
                winning_numbers = item.get('winning_numbers', '')
                if not winning_numbers: continue
                
                parts = winning_numbers.split()
                
                # Tratamento robusto para os dois jogos
                if len(parts) >= 6:
                    whites = [int(n) for n in parts[:5]]
                    special = int(parts[5])
                else:
                    # Caso a Mega Ball venha em campo separado (comum na API MM)
                    whites = [int(n) for n in parts]
                    special = int(item.get('mega_ball', 0))

                # Multiplicador
                m_raw = str(item.get('multiplier', '1')).lower().replace('x', '').strip()
                multiplier = int(float(m_raw)) if m_raw.isdigit() else 1

                # Formato Compacto (d, w, s, m, t)
                processed_list.append({
                    "d": draw_date,
                    "w": whites,
                    "s": special,
                    "m": multiplier,
                    "t": 0 if game_type == "pb" else 1
                })
            except Exception as e:
                continue

        # SALVANDO ARQUIVOS
        if processed_list:
            # 1. Recentes (10 com Payouts)
            recent = [dict(item, p=format_payouts(game_type)) for item in processed_list[:10]]
            with open(f'{game_type}_recent.json', 'w') as f:
                json.dump(recent, f, indent=2)

            # 2. Histórico (Sem Payouts)
            with open(f'{game_type}_history.json', 'w') as f:
                json.dump(processed_list, f, indent=2)
            
            print(f"✅ Arquivos de {game_type} atualizados.")
        else:
            print(f"⚠️ Nenhum dado processado para {game_type}.")

    except Exception as e:
        print(f"❌ Erro fatal {game_type}: {e}")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
