import requests
from datetime import datetime, timedelta
from decimal import Decimal
import time
import random
import os

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

def estrategia_padrao(session, secret, session_token, currency, user_seed, saldo_inicial):
    """Implementação da estratégia principal com:
       - Parada ao ganhar 1% ou perder 10% do saldo inicial.
       - Gatilho para aposta única definido por 'n' (aleatório entre 4 e 8) que é redefinido após cada vitória na aposta única.
    """
    
    sequencia = []
    relatorio_timer = datetime.now() + timedelta(hours=1)
    aposta_count = 0
    n = random.randint(4, 8)  # Define o gatilho inicial para a aposta única, entre 4 e 8 apostas consecutivas iguais.

    while True:
        saldo_atual_float = get_saldo_atual(session, secret, session_token, currency)
        saldo_atual = Decimal(str(saldo_atual_float))
        
        # Condição de parada: ganho de 1% (saldo >= 101% do inicial)
        if saldo_atual >= saldo_inicial * Decimal('1.01'):
            print("Saldo atual atingiu +1% do saldo inicial. Encerrando o loop.")
            break
        
        # Condição de parada: perda de 10% (saldo <= 90% do inicial)
        if saldo_atual <= saldo_inicial * Decimal('0.90'):
            print("Saldo atual caiu abaixo de 90% do saldo inicial (perda de 10%). Encerrando o loop.")
            break

        # Executa a aposta padrão
        bet_obj = PlaceBetObj(
            amount=Decimal('1'),
            chance=Decimal('97'),
            high=random.choice([True, False]),
            guid="unique_guid"
        )
        roll = place_bet(session, bet_obj, user_seed, currency, secret, session_token, Decimal('99.99'))
        
        if roll is not None:
            ganhou = (bet_obj.High and roll > 49.5) or (not bet_obj.High and roll <= 49.5)

            with open("numeros.txt", "a") as file:
                file.write(f"{roll}\n")

            variacao_atual = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100

            print(f"Apostado: {bet_obj.Amount}, Roll: {roll:.4f}, Resultado: {'WIN' if ganhou else 'LOSE'}, Variação: {variacao_atual:.2f}%")

            # Atualiza a sequência com base no resultado do roll
            if roll > 49.5:
                sequencia.append("high")
            else:
                sequencia.append("low")

            if len(sequencia) > 50:
                sequencia.pop(0)

            # Verifica se a sequência acumulada alcançou o tamanho 'n'
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

                            with open("numeros.txt", "a") as file:
                                file.write(f"{roll_unico}\n")

                            saldo_atual_float = get_saldo_atual(session, secret, session_token, currency)
                            saldo_atual = Decimal(str(saldo_atual_float))
                            variacao_atual = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100

                            print(f"Apostado: {aposta_unica.Amount}, Roll: {roll_unico:.4f}, Resultado: {'WIN' if ganhou_unica else 'LOSE'}, Variação: {variacao_atual:.2f}%")

                            # Se ganhar a aposta única, sai do loop e redefine 'n'
                            if ganhou_unica:
                                n = random.randint(4, 8)  # Redefine 'n' para um novo valor aleatório entre 4 e 8
                                break
                            else:
                                aposta_unica_valor *= 2

                    # Limpa a sequência para evitar múltiplos gatilhos consecutivos
                    sequencia.clear()

        aposta_count += 1
        time.sleep(random.uniform(0.5, 3.0))  # Intervalo aleatório entre apostas

        if datetime.now() >= relatorio_timer:
            variacao = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100
            print(f"[Relatório] Saldo: {saldo_atual:.2f}, Variação: {variacao:.2f}%, Apostas: {aposta_count}")
            relatorio_timer = datetime.now() + timedelta(hours=1)

# Início do programa
if __name__ == '__main__':
    session, secret, session_token, currency, user_seed, balance_inicial = login_bitvest("santos01", "Lorota15!")

    if session and secret and session_token and currency and user_seed:
        estrategia_padrao(session, secret, session_token, currency, user_seed, Decimal(str(balance_inicial)))
    else:
        print("Falha na autenticação. Não foi possível iniciar o loop.")

