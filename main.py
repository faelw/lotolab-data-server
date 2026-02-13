import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURAÇÕES ---
# URLs Histórico (Mantendo o que já funciona para os números)
PB_URL_HISTORY = "https://data.ny.gov/resource/d6yy-mqv8.json?$limit=1000&$order=draw_date DESC"
MM_URL_HISTORY = "https://data.ny.gov/resource/5xaw-6ayf.json?$limit=1000&$order=draw_date DESC"

# URL para pegar o JACKPOT ATUAL (Site estável para scraping)
JACKPOT_SOURCE_URL = "https://www.lottery.net/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- FUNÇÕES AUXILIARES ---

def clean_money_value(text_value):
    """
    Converte textos como '$ 1.2 Billion' para um valor numérico puro para análise.
    Retorna uma tupla: (valor_numerico, texto_formatado)
    Ex: 1.2 Billion -> (1200000000.0, "$1.2 Billion")
    """
    if not text_value:
        return 0.0, "Pending"

    # Remove espaços extras e quebras de linha
    clean_text = text_value.strip().replace('\n', ' ')
    
    # Extrai o número
    number_match = re.search(r'([\d\.]+)', clean_text)
    if not number_match:
        return 0.0, clean_text

    number = float(number_match.group(1))

    # Multiplicador
    multiplier = 1000000 # Padrão Million
    if 'Billion' in clean_text or 'B' in clean_text:
        multiplier = 1000000000
    elif 'Thousand' in clean_text or 'K' in clean_text:
        multiplier = 1000
    
    raw_value = number * multiplier
    return raw_value, clean_text

def get_current_jackpots():
    """
    Faz scraping para pegar o valor atual do prêmio.
    Gera um dicionário com os valores para o App analisar.
    """
    print(f"\n💰 Buscando valores de Jackpot em {JACKPOT_SOURCE_URL}...")
    
    data = {
        "pb": {"raw": 0.0, "display": "TBD", "date": ""},
        "mm": {"raw": 0.0, "display": "TBD", "date": ""}
    }

    try:
        response = requests.get(JACKPOT_SOURCE_URL, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erro ao acessar site de Jackpots: {response.status_code}")
            return data

        soup = BeautifulSoup(response.text, 'html.parser')

        # Lógica de extração baseada na estrutura do lottery.net (classes podem variar, mas a estrutura costuma ser estável)
        # Procurando blocos de jogos
        
        # --- POWERBALL ---
        pb_section = soup.find('a', href='/powerball')
        if pb_section:
            # Tenta encontrar o valor dentro do bloco
            val_tag = pb_section.find_next('span', class_='jackpot-amount')
            date_tag = pb_section.find_next('span', class_='next-draw-date')
            
            if val_tag:
                raw, display = clean_money_value(val_tag.text)
                data["pb"]["raw"] = raw
                data["pb"]["display"] = display
            if date_tag:
                data["pb"]["date"] = date_tag.text.strip()

        # --- MEGA MILLIONS ---
        mm_section = soup.find('a', href='/mega-millions')
        if mm_section:
            val_tag = mm_section.find_next('span', class_='jackpot-amount')
            date_tag = mm_section.find_next('span', class_='next-draw-date')
            
            if val_tag:
                raw, display = clean_money_value(val_tag.text)
                data["mm"]["raw"] = raw
                data["mm"]["display"] = display
            if date_tag:
                data["mm"]["date"] = date_tag.text.strip()

        print(f"✅ Jackpots Encontrados -> PB: {data['pb']['display']} | MM: {data['mm']['display']}")
        return data

    except Exception as e:
        print(f"💥 Erro ao processar Jackpots: {e}")
        return data

# --- FUNÇÕES ORIGINAIS (MANTIDAS) ---

def format_payouts(game_type):
    if game_type == "pb":
        return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$50k", "4+0": "$100"}
    return {"5+1": "Jackpot", "5+0": "$1M", "4+1": "$10k", "4+0": "$500"}

def process_history(url, game_type):
    # (Sua função original de histórico, sem alterações na lógica, apenas renomeada para clareza)
    print(f"\n📡 Processando Histórico: {game_type.upper()}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return

        raw_data = response.json()
        processed = []
        seen_dates = set()

        for item in raw_data:
            try:
                draw_date = item.get("draw_date", "").split("T")[0]
                if not draw_date or draw_date in seen_dates: continue

                win_nums = item.get("winning_numbers", "")
                if not win_nums: continue
                whites = [int(n) for n in win_nums.split()]

                if game_type == "pb":
                    special = int(item.get("powerball", 0))
                    m_raw = str(item.get("power_play", "1"))
                else:
                    special = int(item.get("mega_ball", 0))
                    m_raw = str(item.get("multiplier", "1"))

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
            # Salva Histórico
            with open(f"{game_type}_history.json", "w", encoding="utf-8") as f:
                json.dump(processed, f, indent=2)
            # Salva Recentes
            recent = [dict(item, p=format_payouts(game_type)) for item in processed[:10]]
            with open(f"{game_type}_recent.json", "w", encoding="utf-8") as f:
                json.dump(recent, f, indent=2)
            print(f"✅ {game_type.upper()} Histórico OK: {len(processed)} sorteios.")
    except Exception as e:
        print(f"💥 Erro em {game_type}: {e}")

# --- EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    # 1. Atualiza Histórico (Números e Sorteios passados)
    process_history(PB_URL_HISTORY, "pb")
    process_history(MM_URL_HISTORY, "mm")

    # 2. Atualiza Jackpots (Valor Atual e Próximo Sorteio)
    jackpot_data = get_current_jackpots()
    
    # Salva em um arquivo separado específico para a Home do App
    with open("jackpot_current.json", "w", encoding="utf-8") as f:
        json.dump(jackpot_data, f, indent=2)
        print("✅ Arquivo 'jackpot_current.json' salvo com sucesso.")

    # 3. Log de atualização
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
