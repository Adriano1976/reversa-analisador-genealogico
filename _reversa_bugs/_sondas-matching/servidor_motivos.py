"""A mensagem nova sai MESMO pelo servidor no ar? Prova ponta a ponta.

Nao adianta conferir `matching.py` no disco: quem responde e' o processo, e o Python
carrega o modulo uma vez, na partida. Esta sonda usa o servidor que esta' no ar, escolhe
a arvore e o CSV pela LISTA (sem enviar arquivo nenhum, pelo `gedcom_filename` e pelo
`matches_csv_filename`), roda a analise e conta os motivos no HTML devolvido.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\servidor_motivos.py [url]
"""

import collections
import re
import sys
import urllib.parse
import urllib.request
import http.cookiejar

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/"
ARVORE = "21439b0645133804__Adriano_Santos_V2_tratado.ged"
CSV = "54f4887e89705735__Famílias_Sergipanas.csv"
RAIZ = "Adriano Santos"

ANTIGO = "sem candidatos por sobrenome (abreviação/corrupção?)"
NOVOS = (
    "o sobrenome foi lido como prenome (nome sem sobrenome isolável)",
    "o nome não tem sobrenome (nome único)",
    "sobrenome curto demais para buscar (inicial ou abreviação)",
    "nenhum sobrenome do nome existe no GEDCOM",
)


def main():
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def post(campos):
        dados = urllib.parse.urlencode(campos).encode("utf-8")
        with opener.open(urllib.request.Request(URL, data=dados), timeout=300) as r:
            return r.read().decode("utf-8", "replace")

    print(f"servidor: {URL}")
    print(f"1. escolhendo a arvore {ARVORE!r} da lista")
    corpo = post({"action": "selecionar_arvore", "gedcom_filename": ARVORE})
    print(f"   -> {len(corpo)} bytes; tem o formulario de DNA? {'dna-form' in corpo}")

    print(f"2. rodando a analise com {CSV!r} e raiz {RAIZ!r}")
    corpo = post({"action": "dna_analysis", "gedcom_filename": ARVORE,
                  "matches_csv_filename": CSV, "root_name": RAIZ})

    m = re.search(r"(\d+) conexões encontradas\. (\d+) descartadas\.", corpo)
    print(f"   -> {m.group(0) if m else 'mensagem de resultado nao encontrada'}")

    contagem = collections.Counter()
    for texto in (ANTIGO,) + NOVOS:
        contagem[texto] = corpo.count(f"<td>{texto}</td>")
    score = len(re.findall(r"<td>score insuficiente ou conflito de sobrenome", corpo))
    outros = len(re.findall(r"<td>sem sobrenome em comum \(filtro anti-falso-positivo\)</td>", corpo))
    na_tabela = sum(contagem.values()) + score + outros

    print(f"\ncelulas da coluna Motivo na pagina: {na_tabela}")
    print(f"  {'ANTIGO':<8} {contagem[ANTIGO]:>4}  {ANTIGO}")
    for texto in NOVOS:
        print(f"  {'NOVO':<8} {contagem[texto]:>4}  {texto}")
    print(f"  {'inalterado':<8} {score:>4}  score insuficiente ou conflito de sobrenome (…)")
    print(f"  {'inalterado':<8} {outros:>4}  sem sobrenome em comum (filtro anti-falso-positivo)")

    print()
    if contagem[ANTIGO] == 0 and sum(contagem[t] for t in NOVOS) > 0:
        print("VEREDITO: o servidor no ar ja' responde com os motivos novos.")
    elif contagem[ANTIGO] > 0:
        print("VEREDITO: o servidor no ar ainda responde com o motivo ANTIGO — falta reiniciar.")
    else:
        print("VEREDITO: inconclusivo — nenhuma celula de motivo encontrada.")


if __name__ == "__main__":
    main()
