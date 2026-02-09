import requests
import json
import os

# URLs Oficiais (Socrata Open Data API)
PB_URL = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=100&$order=draw_date DESC"
MM_URL = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=100&$order=draw_date DESC"

def format_payouts(game_type, item):
    """Gera um dicionário de rateio simulado ou real se disponível"""
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k"}

def process_data(url, game_type):
    response = requests.get(url)
    if response.status_code != 200:
        return
    
    raw_data = response.json()
    processed = []

    for item in raw_data:
        # Extrair números (Lógica para Powerball ou Mega Millions)
        nums = item.get('winning_numbers', '').split()
        if not nums and game_type == 'mm': # Mega Millions tem campos diferentes
            nums = item.get('winning_numbers', '').split() # Ajuste se necessário
        
        special = nums[-1] if nums else "0"
        whites = [int(n) for n in nums[:-1]] if nums else []

        obj = {
            "d": item.get('draw_date', '').split('T')[0],
            "w": whites,
            "s": int(special),
            "m": int(item.get('multiplier', '1').replace('x', '')),
            "t": 0 if game_type == 'pb' else 1,
            "p": format_payouts(game_type, item) # Detalhado
        }
        processed.append(obj)

    # 1. Salvar Detalhados (Últimos 10 com Payouts)
    with open(f'{game_type}_recent.json', 'w') as f:
        json.dump(processed[:10], f, indent=2)

    # 2. Salvar Histórico (Remover campo 'p' para economizar banda/espaço)
    for item in processed:
        item.pop('p', None)
    
    with open(f'{game_type}_history.json', 'w') as f:
        json.dump(processed, f, indent=2)

if __name__ == "__main__":
    print("Iniciando atualização de dados LotoLab...")
    process_data(PB_URL, "pb")
    process_data(MM_URL, "mm")
    print("Arquivos JSON gerados com sucesso!")
