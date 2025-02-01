import requests
from datetime import datetime
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
        tmp_chance = max_roll - bet.Chance + Decimal('0.0001') if bet.High else bet.Chance - Decimal('0.0001')

        data = {
            "bet": str(bet.Amount),
            "target": f"{tmp_chance:.4f}",
            "side": "high" if bet.High else "low",
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
            roll = tmp.get('game_result', {}).get('roll', 0)
            return roll
        else:
            print(f"Erro na aposta: {tmp.get('msg')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

# --- Login Mantido Igual ao Código Original ---
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
        print("Erro: Resposta inválida na primeira etapa do login.")
        return None, None, None, None, None, None

    session_token = tmpblogin['data']['session_token']
    secret = tmpblogin['account']['secret']

    update_url = "https://bitvest.io/update.php"
    data = {"c": "99999999", "g[]": "999999999", "k": "0", "m": "99999899", "u": "0"}
    response = session.post(update_url, data=data)
    response.raise_for_status()

    data = {
        "username": username,
        "password": password,
        "token": session_token,
        "secret": secret
    }
    response = session.post(login_url, data=data)
    response.raise_for_status()
    tmpblogin = response.json()

    if 'data' in tmpblogin and tmpblogin['data']['session_token']:
        session_token = tmpblogin['data']['session_token']
        user_seed = tmpblogin['data'].get('current-user-seed', '')

        currency = "tokens"
        balance = float(tmpblogin['data'].get('token-balance', '0').replace(',', ''))

        return session, secret, session_token, currency, user_seed, balance
    else:
        print("Falha ao obter o token de sessão.")
        return None, None, None, None, None, None

# --- Função para Obter Saldo Atual ---
def get_saldo_atual(session, secret, session_token, currency):
    try:
        data = {"type": "secret", "secret": secret, "token": session_token}
        response = session.post("https://bitvest.io/login.php", data=data)
        response.raise_for_status()
        tmplogin = response.json()

        if 'data' in tmplogin:
            return float(tmplogin['data'].get('token-balance', '0').replace(',', ''))
        else:
            return 0
    except requests.exceptions.RequestException:
        return 0

# --- Início do Loop de Apostas ---
session, secret, session_token, currency, user_seed, balance = login_bitvest("error101", "wolfgang")

if session and secret and session_token and currency and user_seed:
    if balance == 0:
        print("Saldo inicial é zero. Encerrando a execução.")
    else:
        n = random.randint(6, 8)  # Número de repetições consecutivas para encerrar
        print(f"Monitorando sequência de {n} valores consecutivos.")

        bet_obj = PlaceBetObj(amount=Decimal('1'), chance=Decimal('97'), high=False, guid="unique_guid")
        ultimos_resultados = []
        aposta_count = 0

        while True:
            bet_obj.High = random.choice([True, False])  # Alterna entre "high" e "low"
            roll = place_bet(session, bet_obj, seed=user_seed, currency=currency, secret=secret, accesstoken=session_token, max_roll=Decimal('99.99'))

            if roll is not None:
                with open("numeros.txt", "a") as file:
                    file.write(f"{roll}\n")

                ultimos_resultados.append(roll)
                if len(ultimos_resultados) > n:
                    ultimos_resultados.pop(0)  # Mantém apenas os últimos `n` valores

                if len(ultimos_resultados) == n:  # Apenas verifica quando temos `n` valores acumulados
                    acima = all(r > 49.5 for r in ultimos_resultados)
                    abaixo = all(r < 49.5 for r in ultimos_resultados)

                    if acima or abaixo:
                        print(f"Sequência de {n} valores consecutivos detectada!")
                        print(f"Últimos {n} valores: {ultimos_resultados}")
                        break  # Encerra o loop ao detectar a sequência desejada

            aposta_count += 1
            time.sleep(1)  # Aguarda 1 segundo entre as apostas

        saldo_final = get_saldo_atual(session, secret, session_token, currency)
        variacao = ((saldo_final - balance) / balance) * 100

        print(f"Saldo Inicial: {balance:.2f}")
        print(f"Saldo Final: {saldo_final:.2f}")
        print(f"Variação: {variacao:.2f}%")
        print(f"Número total de apostas feitas: {aposta_count}")

else:
    print("Falha na autenticação. Não foi possível iniciar o loop.")

