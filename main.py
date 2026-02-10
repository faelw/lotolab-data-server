import requests
import json

# URLs oficiais (API Socrata - Resultados de NY que servem para todo os EUA)
# Pegamos os últimos 100 para ter um histórico bom para o Analytics
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=100&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=100&$order=draw_date DESC"

def format_payouts(game_type):
    """Retorna a estrutura de prêmios padrão (Rateio)"""
    if game_type == "pb":
        return {
            "Grand Prize": "Jackpot",
            "Match 5 + 0": "$1,000,000",
            "Match 4 + 1": "$50,000",
            "Match 4 + 0": "$100",
            "Match 3 + 1": "$100"
        }
    else:
        return {
            "Jackpot": "Grand Prize",
            "Match 5 + 0": "$1,000,000",
            "Match 4 + MB": "$10,000",
            "Match 4 + 0": "$500",
            "Match 3 + MB": "$200"
        }

def process_game(url, game_type):
    print(f"Buscando dados de: {game_type.upper()}...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erro ao acessar API: {response.status_code}")
        return

    raw_data = response.json()
    processed_list = []

    for item in raw_data:
        try:
            # Tratamento específico para Mega Millions (campos podem variar na API)
            winning_numbers = item.get('winning_numbers', '')
            mega_ball = item.get('mega_ball', None)
            
            nums = winning_numbers.split()
            
            if not nums: continue

            # Se for Mega Millions e a Mega Ball vier num campo separado
            if game_type == "mm" and mega_ball:
                whites = [int(n) for n in nums]
                special = int(mega_ball)
            else:
                # Padrão Powerball ou MM com tudo na mesma string
                whites = [int(n) for n in nums[:-1]]
                special = int(nums[-1])

            # Criando o objeto no padrão comprimido LotoLab
            obj = {
                "d": item.get('draw_date', '').split('T')[0], # Data
                "w": whites,                                  # White Balls
                "s": special,                                 # Special Ball
                "m": int(item.get('multiplier', '1').lower().replace('x', '')), # Multiplier
                "t": 0 if game_type == "pb" else 1            # Type (0=PB, 1=MM)
            }
            processed_list.append(obj)
        except Exception as e:
            print(f"Erro ao processar sorteio: {e}")

    # --- 1. GERAR ARQUIVO DETALHADO (Últimos 10 com Rateio) ---
    recent_data = []
    for i, item in enumerate(processed_list[:10]):
        # Adiciona o campo de rateio 'p' apenas nos 10 recentes
        item_with_payout = item.copy()
        item_with_payout["p"] = format_payouts(game_type)
        recent_data.append(item_with_payout)
    
    with open(f'{game_type}_recent.json', 'w') as f:
        json.dump(recent_data, f, indent=2)

    # --- 2. GERAR ARQUIVO HISTÓRICO (Resumido para Analytics) ---
    # Aqui usamos a lista original (sem o campo 'p')
    with open(f'{game_type}_history.json', 'w') as f:
        json.dump(processed_list, f, indent=2)

    print(f"Arquivos para {game_type} gerados!")

if __name__ == "__main__":
    process_game(PB_URL, "pb")
    process_game(MM_URL, "mm")
    print("\nAtualização concluída com sucesso!")
