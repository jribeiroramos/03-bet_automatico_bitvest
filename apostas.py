# apostas.py
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import time
import random

class PlaceBetObj:
    def __init__(self, amount, chance, high, guid):
        self.Amount = amount
        self.Chance = chance
        self.High = high
        self.Guid = guid

def place_bet(session, bet, seed, currency, secret, accesstoken, max_roll):
    try:
        amount = bet.Amount
        chance = bet.Chance
        high = bet.High

        tmp_chance = max_roll - chance + Decimal('0.0001') if high else chance - Decimal('0.0001')

        data = {
            "bet": str(amount),
            "target": f"{tmp_chance:.4f}",
            "side": "high" if high else "low",
            "act": "play_dice",
            "currency": currency,
            "secret": secret,
            "token": accesstoken,
            "user_seed": seed,
            "v": "101"
        }

        response = session.post("https://bitvest.io/action.php", data=data)
        response.raise_for_status()
        tmp = response.json()

        if tmp.get('success'):
            return tmp.get('game_result', {}).get('roll')
        else:
            return None
    except:
        return None

def login_bitvest(username, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "DiceBot",
        "Accept-Encoding": "gzip, deflate"
    })

    login_url = "https://bitvest.io/login.php"
    data = {"type": "secret"}
    response = session.post(login_url, data=data)
    response.raise_for_status()
    tmpblogin = response.json()

    if 'data' not in tmpblogin or 'session_token' not in tmpblogin['data']:
        return None, None, None, None, None, None

    session_token = tmpblogin['data']['session_token']
    secret = tmpblogin['account']['secret']

    update_url = "https://bitvest.io/update.php"
    data = {"c": "99999999", "g[]": "999999999", "k": "0", "m": "99999899", "u": "0"}
    session.post(update_url, data=data)

    data = {"username": username, "password": password, "token": session_token, "secret": secret}
    response = session.post(login_url, data=data)
    response.raise_for_status()
    tmpblogin = response.json()

    if 'data' in tmpblogin and tmpblogin['data'].get('session_token'):
        session_token = tmpblogin['data']['session_token']
        user_seed = tmpblogin['data'].get('current-user-seed', '')
        currency = "tokens"
        balance = float(tmpblogin['data'].get('token-balance', '0').replace(',', ''))
        return session, secret, session_token, currency, user_seed, balance
    else:
        return None, None, None, None, None, None

def get_saldo_atual(session, secret, session_token, currency):
    try:
        data = {"type": "secret", "secret": secret, "token": session_token}
        response = session.post("https://bitvest.io/login.php", data=data)
        response.raise_for_status()
        tmp = response.json()

        if 'data' in tmp:
            data_resp = tmp['data']
            if currency.lower() == "tokens":
                return float(data_resp.get('token-balance', '0').replace(',', ''))
        return 0.0
    except:
        return 0.0

def estrategia_padrao(session, secret, session_token, currency, user_seed, saldo_inicial, emit_update):
    """
    Estratégia de apostas:
      - Para cada aposta, atualiza estatísticas:
          - saldo_inicial, saldo_atual, variação (%),
          - contagem de rolls >49.5 (roll_acima) e <=49.5 (roll_abaixo)
      - Emite atualizações via 'emit_update' (callback passado pelo app)
    """
    sequencia = []
    relatorio_timer = datetime.now() + timedelta(hours=1)
    aposta_count = 0
    n = random.randint(4, 8)  # gatilho para aposta única

    # Contadores para os gráficos
    roll_acima = 0
    roll_abaixo = 0

    while True:
        saldo_atual_float = get_saldo_atual(session, secret, session_token, currency)
        saldo_atual = Decimal(str(saldo_atual_float))
        
        # Paradas: ganho de 1% ou perda de 10%
        if saldo_atual >= saldo_inicial * Decimal('2.85'):
            emit_update(f"Saldo +3% atingido: {saldo_atual}. Encerrando.", {
                "saldo_inicial": float(saldo_inicial),
                "saldo_atual": float(saldo_atual),
                "variacao": float(((saldo_atual - saldo_inicial) / saldo_inicial) * 100)
            })
            break
        
        if saldo_atual <= saldo_inicial * Decimal('0.90'):
            emit_update(f"Saldo -10% atingido: {saldo_atual}. Encerrando.", {
                "saldo_inicial": float(saldo_inicial),
                "saldo_atual": float(saldo_atual),
                "variacao": float(((saldo_atual - saldo_inicial) / saldo_inicial) * 100)
            })
            break

        # Aposta padrão
        bet_obj = PlaceBetObj(
            amount=Decimal('1'),
            chance=Decimal('97'),
            high=random.choice([True, False]),
            guid="unique_guid"
        )
        roll = place_bet(session, bet_obj, user_seed, currency, secret, session_token, Decimal('99.99'))
        
        if roll is not None:
            ganhou = (bet_obj.High and roll > 49.5) or (not bet_obj.High and roll <= 49.5)
            mensagem = f"Apostado: {bet_obj.Amount}, Roll: {roll:.4f}, Resultado: {'WIN' if ganhou else 'LOSE'}"
            # Atualiza os contadores para o gráfico
            if roll > 49.5:
                roll_acima += 1
                sequencia.append("high")
            else:
                roll_abaixo += 1
                sequencia.append("low")
            
            if len(sequencia) > 50:
                sequencia.pop(0)
            
            # Verifica gatilho para aposta única
            if len(sequencia) >= n:
                recorte = sequencia[-n:]
                if all(x == "high" for x in recorte) or all(x == "low" for x in recorte):
                    ultima_aposta = recorte[-1]
                    aposta_unica_tipo = (ultima_aposta == "low")
                    aposta_unica_valor = saldo_atual * Decimal('0.005')
                    
                    while True:
                        aposta_unica = PlaceBetObj(
                            amount=aposta_unica_valor,
                            chance=Decimal('49.5'),
                            high=aposta_unica_tipo,
                            guid="aposta_unica"
                        )
                        roll_unico = place_bet(session, aposta_unica, user_seed, currency, secret, session_token, Decimal('99.99'))
                        if roll_unico is not None:
                            ganhou_unica = (aposta_unica.High and roll_unico > 49.5) or (not aposta_unica.High and roll_unico <= 49.5)
                            mensagem_unica = f"Aposta Única: {aposta_unica.Amount}, Roll: {roll_unico:.4f}, Resultado: {'WIN' if ganhou_unica else 'LOSE'}"
                            emit_update(mensagem_unica)
                            
                            if ganhou_unica:
                                n = random.randint(4, 8)  # redefine o gatilho
                                break
                            else:
                                aposta_unica_valor *= 2
                    sequencia.clear()
            
            aposta_count += 1

            # Atualiza estatísticas para o dashboard
            variacao = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100
            stats = {
                "saldo_inicial": float(saldo_inicial),
                "saldo_atual": float(saldo_atual),
                "variacao": float(variacao),
                "roll_acima": roll_acima,
                "roll_abaixo": roll_abaixo,
                "aposta_count": aposta_count
            }
            emit_update(f"captchas realizadas: {aposta_count} | Saldo atual: {saldo_atual}", stats)
        
        time.sleep(random.uniform(0.5, 3.0))
        
        if datetime.now() >= relatorio_timer:
            variacao = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100
            emit_update(f"[Relatório] Saldo: {saldo_atual}, Apostas: {aposta_count}", {
                "saldo_inicial": float(saldo_inicial),
                "saldo_atual": float(saldo_atual),
                "variacao": float(variacao)
            })
            relatorio_timer = datetime.now() + timedelta(hours=1)
def progressive_apostas(resultados):
    """
    Simula uma sequência de apostas usando uma estratégia de progressão (Martingale)
    com base em um array (lista) de resultados.

    Parâmetros:
      resultados (list): Lista de 10 valores inteiros (0 ou 1), onde:
                          0 => perda, 1 => vitória.

    Lógica:
      - Inicia com uma aposta de 1.
      - Se o resultado for 1 (vitória), assume-se um lucro igual ao valor apostado
        (e a aposta é reiniciada para 1).
      - Se o resultado for 0 (perda), a aposta é perdida e para a próxima rodada
        o valor a apostar é dobrado.
    
    Retorna:
      Uma lista de dicionários, cada um contendo:
        - 'round': número da rodada (1 a 10)
        - 'outcome': o resultado da rodada (0 ou 1)
        - 'bet': valor apostado nessa rodada
        - 'profit': lucro (positivo) ou prejuízo (negativo) nessa rodada
        - 'cumulative_profit': lucro acumulado até aquela rodada
    """
    bet = 1
    cumulative_profit = 0
    simulacao = []
    
    for i, resultado in enumerate(resultados):
        if resultado == 1:
            # Vitória: ganha um valor igual à aposta; reinicia a aposta para 1
            profit = bet
            cumulative_profit += profit
            simulacao.append({
                "round": i + 1,
                "outcome": resultado,
                "bet": bet,
                "profit": profit,
                "cumulative_profit": cumulative_profit
            })
            bet = 1  # reinicia a aposta
        else:
            # Perda: perde o valor apostado; dobra a aposta para a próxima rodada
            profit = -bet
            cumulative_profit += profit
            simulacao.append({
                "round": i + 1,
                "outcome": resultado,
                "bet": bet,
                "profit": profit,
                "cumulative_profit": cumulative_profit
            })
            bet *= 2  # dobra a aposta
    
    return simulacao

if __name__ == '__main__':
    # Execução para testes locais (não será chamada se importado pelo app.py)
    session, secret, session_token, currency, user_seed, balance_inicial = login_bitvest("santos01", "Lorota15!")
    if session and secret and session_token and currency and user_seed:
        estrategia_padrao(session, secret, session_token, currency, user_seed, Decimal(str(balance_inicial)), print)
    else:
        print("Falha na autenticação. Não foi possível iniciar o loop.")

