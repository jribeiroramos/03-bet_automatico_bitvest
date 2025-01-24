import requests
from datetime import datetime
from decimal import Decimal

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
            game_result = tmp.get('game_result', {})
            player_seed = tmp.get('player_seed', '')
            nonce = int(player_seed.split("|")[1]) if '|' in player_seed else 0

            res_bet = Bet(
                amount=bet.Amount,
                date=datetime.now(),
                chance=bet.Chance,
                high=bet.High,
                clientseed=seed,
                serverhash=tmp.get('server_hash', ''),
                serverseed=tmp.get('server_seed', ''),
                roll=game_result.get('roll', 0),
                profit=Decimal(game_result.get('win', 0)) - bet.Amount if game_result.get('win', 0) != 0 else -bet.Amount,
                nonce=nonce,
                bet_id=tmp.get('game_id', 0),
                currency=currency,
                guid=bet.Guid
            )
            return res_bet.Roll, res_bet.Profit
        else:
            print(f"Erro na aposta: {tmp.get('msg')}")
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
    except Exception as e:
        print(f"Erro desconhecido: {e}")
    return None, None

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
    session_token = tmpblogin['data']['session_token']
    secret = tmpblogin['account']['secret']

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
        balance = float(tmpblogin['data'].get('balance', '0').replace(',', ''))

        return session, secret, session_token, currency, user_seed, balance
    else:
        print("Falha ao obter o token de sessão.")
        return None, None, None, None, None, None

def get_saldo_atual(session, secret, session_token, currency):
    data = {
        "type": "secret",
        "secret": secret,
        "token": session_token
    }
    response = session.post("https://bitvest.io/login.php", data=data)
    response.raise_for_status()
    tmplogin = response.json()
    
    balance = 0
    if 'data' in tmplogin:
        if currency.lower() == "tokens":
            balance = float(tmplogin['data'].get('balance', 0))
        else:
            balance = float(tmplogin['data'].get('token-balance', '0').replace(',', ''))            
    return balance

# Loop principal removido
session, secret, session_token, currency, user_seed, balance = login_bitvest("santos01", "Lorota15!")

if session and secret and session_token and currency and user_seed:
    if balance == 0:
        print("Saldo inicial é zero. Encerrando a execução para evitar divisão por zero.")
    else:
        # Cria o objeto de aposta com valores fixos
        bet_obj = PlaceBetObj(amount=Decimal('10'), chance=Decimal('49.5'), high=False, guid="unique_guid")
        
        # Executa uma única aposta
        roll, profit = place_bet(session, bet_obj, seed=user_seed, currency=currency, secret=secret, accesstoken=session_token, max_roll=Decimal('99.99'))
        
        if roll is not None:
            print(f"Aposta realizada!")
            print(f"Roll (Número gerado): {roll}")
            print(f"Profit (Lucro/Prejuízo): {profit:.2f}")
        else:
            print("A aposta não foi concluída devido a um erro.")
        
        # Exibe o saldo final após a aposta
        saldo_final = get_saldo_atual(session, secret, session_token, currency)
        variacao = ((saldo_final - balance) / balance) * 100
        
        print(f"Saldo Inicial: {balance:.2f}")
        print(f"Saldo Final: {saldo_final:.2f}")
        print(f"Variação: {variacao:.2f}%")
else:
    print("Falha na autenticação. Não foi possível realizar a aposta.")

