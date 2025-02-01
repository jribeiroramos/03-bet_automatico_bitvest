# analise_numeros.py
import statistics
from decimal import Decimal, InvalidOperation

def analisar_numeros(arquivo="numeros.txt"):
    """
    Lê os valores de 'arquivo' (um valor por linha) e retorna um dicionário com:
      - Total de valores lidos
      - Média, mediana e desvio-padrão
      - Contagem e porcentagem de valores > 49.5 e <= 49.5
      - Top 5 menores e Top 5 maiores (com frequências)
      - Valor mais frequente (agrupado em 2 casas decimais) e sua frequência
    """
    valores = []
    try:
        with open(arquivo, "r") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        valor = float(Decimal(linha))
                        valores.append(valor)
                    except (ValueError, InvalidOperation):
                        pass
    except FileNotFoundError:
        return {"erro": f"Arquivo '{arquivo}' não encontrado."}

    if not valores:
        return {"erro": "Nenhum valor válido encontrado."}

    media = statistics.mean(valores)
    mediana = statistics.median(valores)
    desvio_padrao = statistics.pstdev(valores)

    total = len(valores)
    acima_49_5 = sum(1 for v in valores if v > 49.5)
    abaixo_ou_igual_49_5 = total - acima_49_5
    perc_acima = (acima_49_5 / total) * 100
    perc_abaixo_igual = (abaixo_ou_igual_49_5 / total) * 100

    # Frequências (agrupando em 2 casas decimais)
    frequencias = {}
    for v in valores:
        chave = round(v, 2)
        frequencias[chave] = frequencias.get(chave, 0) + 1

    valor_mais_frequente = max(frequencias, key=frequencias.get)
    freq_max = frequencias[valor_mais_frequente]

    ordenados_por_valor = sorted(frequencias.items(), key=lambda x: x[0])
    top5_menores = ordenados_por_valor[:5]
    top5_maiores = ordenados_por_valor[-5:]

    stats = {
        "total_valores": total,
        "media": media,
        "mediana": mediana,
        "desvio_padrao": desvio_padrao,
        "acima_49_5": acima_49_5,
        "perc_acima": perc_acima,
        "abaixo_ou_igual_49_5": abaixo_ou_igual_49_5,
        "perc_abaixo_igual": perc_abaixo_igual,
        "valor_mais_frequente": valor_mais_frequente,
        "freq_max": freq_max,
        "top5_menores": top5_menores,
        "top5_maiores": top5_maiores
    }
    return stats

if __name__ == "__main__":
    stats = analisar_numeros("numeros.txt")
    if "erro" in stats:
        print(stats["erro"])
    else:
        print(stats)

