# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import threading, time
from decimal import Decimal
from apostas import login_bitvest, estrategia_padrao
import analise_numeros  # módulo de análise dos números

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUA_CHAVE_SECRETA'
socketio = SocketIO(app)

# Variável global para armazenar os dados do dashboard
global_status = {
    "logs": [],
    "saldo_inicial": None,
    "saldo_atual": None,
    "variacao": None,
    "roll_acima": 0,
    "roll_abaixo": 0,
    "aposta_count": 0,
    "analise_numeros": {}  # Aqui serão armazenadas as estatísticas do arquivo numeros.txt
}

def emit_update(mensagem, stats=None):
    """Atualiza global_status e emite os dados via SocketIO."""
    if stats:
        global_status.update(stats)
    global_status["logs"].append(mensagem)
    socketio.emit('update', global_status)
    print(mensagem)

def run_betting_engine(username, password):
    session_bitvest, secret, session_token, currency, user_seed, balance_inicial = login_bitvest(username, password)
    if not (session_bitvest and secret and session_token and currency and user_seed):
        emit_update("Falha na autenticação.")
        return
    threading.Thread(
        target=estrategia_padrao,
        args=(session_bitvest, secret, session_token, currency, user_seed, Decimal(str(balance_inicial)), emit_update)
    ).start()

def update_analysis_periodically():
    """Atualiza periodicamente as estatísticas do arquivo 'numeros.txt'."""
    while True:
        try:
            stats = analise_numeros.analisar_numeros("numeros.txt")
            # Atualiza global_status se não houver erro
            if "erro" not in stats:
                global_status["analise_numeros"] = stats
                socketio.emit("update", global_status)
        except Exception as e:
            print("Erro na atualização de análise:", e)
        time.sleep(30)  # Atualiza a cada 30 segundos

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        run_betting_engine(username, password)
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/statistics')
def statistics():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('statistics.html')

if __name__ == '__main__':
    # Inicia a thread para atualizar as estatísticas
    threading.Thread(target=update_analysis_periodically, daemon=True).start()
    socketio.run(app, debug=True)

