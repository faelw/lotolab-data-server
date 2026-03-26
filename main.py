import requests
from bs4 import BeautifulSoup
import json
import os

def update_json(file_path, url):
    # 1. Scraping do Jackpot
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Seletor baseado na estrutura da Texas Lottery
    try:
        jackpot_val = soup.find('td', {'data-th': 'Advertised Jackpot'}).text.strip()
    except:
        print("Erro ao extrair Jackpot")
        return

    # 2. Carregar seu arquivo local (ex: mm_recent.json)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Atualiza o jackpot do sorteio mais recente (topo da lista)
        if data and isinstance(data, list):
            data[0]['jackpot'] = jackpot_val
            
            # Salvar de volta
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Sucesso: {file_path} atualizado com {jackpot_val}")

# Execução para Mega Millions
update_json('mm_recent.json', 'https://www.texaslottery.com/export/sites/lottery/Games/Mega_Millions/Estimated_Jackpot.html')
