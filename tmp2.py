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

class Bet:
    def __init__(self, amount, date, chance, high, clientseed, serverhash, serverseed, roll, profit, nonce, bet_id, currency, guid):
        self.Amount = amount
        self.date = date
        self.Chance = chance
        self.high = high
        self.clientseed = clientseed
        self.serverhash = serverhash
        self.serverseed = serverseed
        self.Roll = roll
        self.Profit = profit
        self.nonce = nonce
        self.Id = bet_id
        self.Currency = currency
        self.Guid = guid

def place_bet(session, bet, seed, currency, secret, accesstoken, max_roll):
    """
    Envia a aposta para o site e retorna apenas o 'roll' (número gerado).
    Sem prints adicionais.
    """
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
            # Se não for sucesso, retorna None
            return None

    except:
        return None

def login_bitvest(username, password):
    """
    Mantido para garantir o login funcional,
    apenas removendo prints desnecessários.
    """
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

    # Atualiza estado
    update_url = "https://bitvest.io/update.php"
    data = {
        "c": "99999999",
        "g[]": "999999999",
        "k": "0",
        "m": "99999899",
        "u": "0"
    }
    session.post(update_url, data=data)

    # Completa login
    data = {
        "username": username,
        "password": password,
        "token": session_token,
        "secret": secret
    }
    response = session.post(login_url, data=data)
    response.raise_for_status()
    tmpblogin = response.json()

    if 'data' in tmpblogin and tmpblogin['data'].get('session_token'):
        session_token = tmpblogin['data']['session_token']
        user_seed = tmpblogin['data'].get('current-user-seed', '')

        # Ajusta moeda
        currency = "tokens"
        balance_str = tmpblogin['data'].get('token-balance', '0')
        balance = float(balance_str.replace(',', ''))
        return session, secret, session_token, currency, user_seed, balance

    else:
        return None, None, None, None, None, None

def get_saldo_atual(session, secret, session_token, currency):
    """
    Retorna o saldo atual (float) sem prints extras.
    """
    try:
        data = {
            "type": "secret",
            "secret": secret,
            "token": session_token
        }
        response = session.post("https://bitvest.io/login.php", data=data)
        response.raise_for_status()
        tmp = response.json()

        if 'data' in tmp:
            data_resp = tmp['data']
            if currency.lower() == "tokens":
                return float(data_resp.get('token-balance', '0').replace(',', ''))
            # se quiser ethers, litecoins, dogecoins etc, implemente aqui
        return 0.0
    except:
        return 0.0

# Remove arquivo numeros.txt no início
if os.path.exists("numeros.txt"):
    os.remove("numeros.txt")

session, secret, session_token, currency, user_seed, balance_inicial = login_bitvest("error101", "wolfgang")

if session and secret and session_token and currency and user_seed:
    if balance_inicial == 0:
        print("Saldo inicial é zero. Encerrando.")
    else:
        saldo_inicial = Decimal(str(balance_inicial))
        meta_lucro = saldo_inicial * Decimal('1.24')   # +24%
        limite_perda = saldo_inicial * Decimal('0.97') # -3%
        sequencia = []
        relatorio_timer = datetime.now() + timedelta(hours=1)
        aposta_count = 0

        while True:
            saldo_atual_float = get_saldo_atual(session, secret, session_token, currency)
            saldo_atual = Decimal(str(saldo_atual_float))

            # Verifica limites
            if saldo_atual >= meta_lucro:
                print("Meta de +24% atingida. Encerrando.")
                break
            if saldo_atual <= limite_perda:
                print("Limite de -3% atingido. Encerrando.")
                break

            # Aposta normal
            bet_obj = PlaceBetObj(
                amount=Decimal('1'),
                chance=Decimal('97'),
                high=random.choice([True, False]),
                guid="unique_guid"
            )
            roll = place_bet(session, bet_obj, user_seed, currency, secret, session_token, Decimal('99.99'))
            if roll is not None:
                # Decide se ganhou ou perdeu
                ganhou = (bet_obj.High and roll > 49.5) or (not bet_obj.High and roll <= 49.5)

                # Grava no arquivo
                with open("numeros.txt", "a") as file:
                    file.write(f"{roll}\n")

                # Calcula variação atual
                variacao_atual = ((saldo_atual - saldo_inicial)/saldo_inicial)*100

                # Imprime somente: valor apostado, número, resultado e % variação
                print(f"Apostado: {bet_obj.Amount}, Roll: {roll:.4f}, Resultado: {'WIN' if ganhou else 'LOSE'}, Variação: {variacao_atual:.2f}%")

                # Atualiza sequência
                if roll > 49.5:
                    sequencia.append("high")
                else:
                    sequencia.append("low")

                if len(sequencia) > 50:
                    sequencia.pop(0)

                # Checa sequência [6..8]
                n = random.randint(6, 8)
                if len(sequencia) >= n:
                    recorte = sequencia[-n:]
                    if all(x == "high" for x in recorte) or all(x == "low" for x in recorte):
                        # Sequência detectada => aposta única
                        ultima_aposta = recorte[-1]
                        aposta_unica_tipo = (ultima_aposta == "low")  # se seq for low => bet high
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

                                # Grava no arquivo
                                with open("numeros.txt", "a") as file:
                                    file.write(f"{roll_unico}\n")

                                # Recalcula saldo
                                saldo_atual_float = get_saldo_atual(session, secret, session_token, currency)
                                saldo_atual = Decimal(str(saldo_atual_float))
                                variacao_atual = ((saldo_atual - saldo_inicial)/saldo_inicial)*100

                                print(f"Apostado: {aposta_unica.Amount}, Roll: {roll_unico:.4f}, Resultado: {'WIN' if ganhou_unica else 'LOSE'}, Variação: {variacao_atual:.2f}%")

                                if ganhou_unica:
                                    break
                                else:
                                    aposta_unica_valor *= 2

                        # Limpa sequência
                        sequencia.clear()

            aposta_count += 1
            time.sleep(1)

            # Relatório de 1h
            if datetime.now() >= relatorio_timer:
                variacao = ((saldo_atual - saldo_inicial) / saldo_inicial) * 100
                print(f"[Relatório] Saldo: {saldo_atual:.2f}, Variação: {variacao:.2f}%, Apostas: {aposta_count}")
                relatorio_timer = datetime.now() + timedelta(hours=1)

        # Fim do loop principal
        saldo_final_float = get_saldo_atual(session, secret, session_token, currency)
        saldo_final = Decimal(str(saldo_final_float))
        variacao_final = ((saldo_final - saldo_inicial) / saldo_inicial) * 100
        print(f"\n--- FIM ---\nSaldo Inicial: {saldo_inicial:.2f} | Saldo Final: {saldo_final:.2f} | Variação: {variacao_final:.2f}% | Apostas: {aposta_count}")

else:
    print("Falha na autenticação. Não foi possível iniciar o loop.")

