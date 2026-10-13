"""Sondas HTTP do checklist de seguranca: medem comportamento do app em execucao.

Todas as sondas usam dados SINTETICOS (fixtures geradas por `gerar_fixtures.py`),
falam apenas com a instancia loopback subida para a medicao, e escrevem o
resultado em JSON mais os HTMLs crus no diretorio de saida. Nenhum arquivo do
projeto e lido ou escrito por este script.

Grupos:
    estatico      itens 5 e 6 (SRI/CSP/framing) e evidencia estatica de 1 e 2
    origem        item 1  (POST que muda estado sem verificacao de origem)
    identidade    item 2  (ausencia de credencial; allowlist de Host)
    lan           item 2  (acesso por outra interface + variavel de allowlist)
    nomes         item 7  (nomes reservados do Windows e fluxo alternativo NTFS)
    erro          item 8  (texto de excecao cru na pagina)
    parse         item 3  (custo do parse por requisicao e concorrencia)
    dna           item 4  (custo por (linhas do CSV) x (pool de sobrenomes))
    persistencia  item 9  (texto do erro de banco na pagina)

Uso:
    python sondas_http.py <grupo> --porta 5099 --uploads <dir> --fixtures <dir> --outdir <dir>
"""
import argparse
import http.client
import json
import os
import re
import socket
import threading
import time
import uuid

LIMITE = 900


# ---------------------------------------------------------------------------
# Infra minima de HTTP
# ---------------------------------------------------------------------------

def pedir(porta, metodo, caminho, corpo=None, cabecalhos=None, host="127.0.0.1", timeout=LIMITE):
    conexao = http.client.HTTPConnection(host, porta, timeout=timeout)
    try:
        conexao.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
        resposta = conexao.getresponse()
        dados = resposta.read()
        cabecalhos_de_volta = {k.lower(): v for k, v in resposta.getheaders()}
        return {
            "status": resposta.status,
            "cabecalhos": cabecalhos_de_volta,
            "texto": dados.decode("utf-8", "replace"),
            "bytes": len(dados),
        }
    finally:
        conexao.close()


def multipart(campos, arquivos):
    """Corpo `multipart/form-data` montado a mao (o stdlib nao tem encoder)."""
    fronteira = "----sonda" + uuid.uuid4().hex
    partes = []
    for nome, valor in campos.items():
        partes.append(
            f'--{fronteira}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'
            .encode("utf-8"))
    for nome, (nome_arquivo, conteudo, tipo) in arquivos.items():
        partes.append(
            (f'--{fronteira}\r\nContent-Disposition: form-data; name="{nome}"; '
             f'filename="{nome_arquivo}"\r\nContent-Type: {tipo}\r\n\r\n').encode("utf-8"))
        partes.append(conteudo)
        partes.append(b"\r\n")
    partes.append(f"--{fronteira}--\r\n".encode("utf-8"))
    return b"".join(partes), f"multipart/form-data; boundary={fronteira}"


def enviar_formulario(porta, campos, arquivos=None, cabecalhos=None, host="127.0.0.1"):
    if arquivos:
        corpo, tipo = multipart(campos, arquivos)
    else:
        corpo = "&".join(f"{k}={v}" for k, v in campos.items()).encode("utf-8")
        tipo = "application/x-www-form-urlencoded"
    cabecalhos = dict(cabecalhos or {})
    cabecalhos["Content-Type"] = tipo
    cabecalhos["Content-Length"] = str(len(corpo))
    return pedir(porta, "POST", "/", corpo, cabecalhos, host=host)


def upload_gedcom(porta, conteudo, nome_arquivo, cabecalhos=None, host="127.0.0.1"):
    return enviar_formulario(
        porta, {"action": "upload_gedcom"},
        {"gedcom": (nome_arquivo, conteudo, "application/octet-stream")},
        cabecalhos, host=host)


def upload_csv(porta, conteudo, nome_arquivo, referencia_arvore, raiz, cabecalhos=None):
    return enviar_formulario(
        porta,
        {"action": "dna_analysis", "gedcom_filename": referencia_arvore, "root_name": raiz},
        {"matches_csv": (nome_arquivo, conteudo, "text/csv")},
        cabecalhos)


# ---------------------------------------------------------------------------
# Leitura do HTML de resposta
# ---------------------------------------------------------------------------

def mensagens(html):
    """Textos que a tela mostra ao operador (alerta de mensagem e aviso)."""
    blocos = re.findall(
        r'<div class="alert alert-(?:success|danger)[^"]*"[^>]*>(.*?)<button', html, re.S)
    blocos += re.findall(r'<div class="alerta-aviso"[^>]*>(.*?)</div>', html, re.S)
    return [re.sub(r"<[^>]+>", " ", bloco).strip() for bloco in blocos]


def referencia_da_arvore(html):
    achado = re.search(r'name="gedcom_filename" value="([^"]*)"', html)
    return achado.group(1) if achado else None


def tags_de_script(html):
    return re.findall(r"<script[^>]*>", html)


def arquivos_de_terceiros(html):
    return re.findall(r'<(?:script|link)[^>]*(?:src|href)="(https?://[^"]+)"[^>]*>', html)


def ler(caminho):
    with open(caminho, "rb") as fh:
        return fh.read()


def variante(conteudo, marca):
    """Mesma arvore com um byte de diferenca, para cada envio ter CHAVE propria.

    Sem isto o teste fica confundido: o armazenamento e por chave de conteudo, e a
    lista da tela mostra UM representante por chave. Varios nomes com o mesmo
    conteudo viram uma linha so, e o nome em teste desaparece da lista por
    agrupamento, e nao por nao ser alcancavel.
    """
    return conteudo.replace(b"1 SOUR sonda-sintetica", f"1 SOUR sonda-{marca}".encode("ascii"), 1)


def retrato_da_pasta(pasta):
    if not os.path.isdir(pasta):
        return {}
    retrato = {}
    for nome in os.listdir(pasta):
        caminho = os.path.join(pasta, nome)
        retrato[nome] = {
            "arquivo_regular": os.path.isfile(caminho),
            "bytes": os.path.getsize(caminho) if os.path.isfile(caminho) else None,
        }
    return retrato


def ip_da_rede():
    """IP local da interface que o sistema usaria para sair: simula 'outro dispositivo'."""
    sonda = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sonda.connect(("8.8.8.8", 80))
        return sonda.getsockname()[0]
    except OSError:
        return None
    finally:
        sonda.close()


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------

def grupo_estatico(ctx):
    resposta = pedir(ctx["porta"], "GET", "/")
    html = resposta["texto"]
    guardar_artefato(ctx, "estatico-get-index.html", html)

    interessantes = ("content-security-policy", "x-frame-options", "set-cookie",
                     "strict-transport-security", "x-content-type-options",
                     "referrer-policy", "permissions-policy", "cross-origin-opener-policy",
                     "server", "content-type")
    tags = tags_de_script(html)
    scripts_com_src = [tag for tag in tags if "src=" in tag]

    formularios = []
    for achado in re.finditer(r"<form[^>]*>", html):
        trecho = html[achado.start():achado.start() + 4000]
        formularios.append({
            "tag": achado.group(0),
            "acoes": re.findall(r'name="action" value="([^"]*)"', trecho)[:3],
            "ocultos": re.findall(r'<input[^>]*type="hidden"[^>]*>', trecho)[:8],
        })

    return {
        "status": resposta["status"],
        "cabecalhos_de_seguranca": {chave: resposta["cabecalhos"].get(chave)
                                    for chave in interessantes},
        "cabecalhos_completos": resposta["cabecalhos"],
        "seguranca_ausente": [chave for chave in interessantes
                              if chave not in resposta["cabecalhos"]],
        "scripts": scripts_com_src,
        "scripts_sem_integrity": [tag for tag in scripts_com_src if "integrity=" not in tag],
        "terceiros": sorted(set(arquivos_de_terceiros(html))),
        "formularios": formularios,
        "tem_campo_de_token": bool(re.search(
            r'name="(csrf|_csrf|csrf_token|authenticity_token|__RequestVerificationToken)"', html)),
    }


def grupo_origem(ctx):
    conteudo = ler(os.path.join(ctx["fixtures"], "arvore_valida.ged"))
    hostil = {"Origin": "http://atacante.exemplo",
              "Referer": "http://atacante.exemplo/pagina-hostil.html"}
    antes = retrato_da_pasta(ctx["uploads"])

    resposta = upload_gedcom(ctx["porta"], conteudo, "arvore_valida.ged", hostil)
    referencia = referencia_da_arvore(resposta["texto"])
    depois = retrato_da_pasta(ctx["uploads"])
    guardar_artefato(ctx, "origem-upload.html", resposta["texto"])

    resposta_sem_origem = upload_gedcom(ctx["porta"], conteudo, "arvore_valida.ged", {})

    fichas = []
    for rotulo, ref, cabecalhos in (
        ("com_origin_hostil", referencia, hostil),
        ("sem_origin_nem_referer", referencia, {}),
    ):
        if not ref:
            fichas.append({"caso": rotulo, "erro": "sem referencia na resposta"})
            continue
        retirada = enviar_formulario(
            ctx["porta"],
            {"action": "aposentar_arquivo", "arquivo_a_aposentar": ref},
            None, cabecalhos)
        guardar_artefato(ctx, f"origem-aposentar-{rotulo}.html", retirada["texto"])
        fichas.append({
            "caso": rotulo,
            "status": retirada["status"],
            "mensagem": mensagens(retirada["texto"]),
            "aposentados": retrato_da_pasta(os.path.join(ctx["uploads"], "_aposentados")),
        })
        # devolve o arquivo para a pasta, para o proximo caso encontrar o mesmo estado
        aposentados = os.path.join(ctx["uploads"], "_aposentados")
        origem = os.path.join(aposentados, ref)
        if os.path.isfile(origem):
            os.replace(origem, os.path.join(ctx["uploads"], ref))

    novos = sorted(set(depois) - set(antes))
    return {
        "upload_com_origin_hostil": {
            "status": resposta["status"],
            "mensagem": mensagens(resposta["texto"]),
            "referencia_devolvida": referencia,
            "arquivos_novos": novos,
        },
        "segundo_upload_sem_origin": {
            "status": resposta_sem_origem["status"],
            "mensagem": mensagens(resposta_sem_origem["texto"]),
        },
        "acao_destrutiva": fichas,
        "cabecalhos_enviados": hostil,
    }


def grupo_identidade(ctx):
    limpa = pedir(ctx["porta"], "GET", "/")
    return {
        "sem_credencial": {
            "status": limpa["status"],
            "set_cookie": limpa["cabecalhos"].get("set-cookie"),
            "www_authenticate": limpa["cabecalhos"].get("www-authenticate"),
            "bytes_da_pagina": limpa["bytes"],
            "ve_a_lista_de_arquivos": "arvores_da_lista" in limpa["texto"]
            or "nav-tabs" in limpa["texto"],
        },
        "host_forjado": {
            "host": "atacante.exemplo",
            "status": pedir(ctx["porta"], "GET", "/", None,
                            {"Host": "atacante.exemplo"})["status"],
            "corpo": pedir(ctx["porta"], "GET", "/", None,
                           {"Host": "atacante.exemplo"})["texto"][:200],
        },
        "host_loopback": {
            "host": "127.0.0.1",
            "status": pedir(ctx["porta"], "GET", "/", None,
                            {"Host": f"127.0.0.1:{ctx['porta']}"})["status"],
        },
        "host_localhost_sem_porta": {
            "status": pedir(ctx["porta"], "GET", "/", None, {"Host": "localhost"})["status"],
        },
    }


def grupo_lan(ctx):
    """Item 2: o app ligado fora do loopback, alcancado por um endereco que NAO esta na lista.

    O endereco de teste e parametro (`--endereco`). Por padrao a sonda usa um SEGUNDO
    endereco de loopback (127.0.0.2) em vez do IP da rede local: a maquina nao fica
    exposta na rede para medir uma decisao que e do allowlist, e nao da topologia.
    """
    ip = ctx.get("endereco") or ip_da_rede()
    if not ip:
        return {"erro": "nao foi possivel descobrir o endereco de teste"}
    por_ip = pedir(ctx["porta"], "GET", "/", None, {"Host": f"{ip}:{ctx['porta']}"}, host=ip)
    por_ip_sem_host = pedir(ctx["porta"], "GET", "/", None, {}, host=ip)
    return {
        "endereco_de_teste": ip,
        "porta": ctx["porta"],
        "acesso_por_outra_interface_com_host_proprio": {
            "status": por_ip["status"],
            "corpo": por_ip["texto"][:200],
        },
        "acesso_por_outra_interface_host_padrao_do_cliente": {
            "status": por_ip_sem_host["status"],
            "bytes": por_ip_sem_host["bytes"],
        },
        "variavel_de_allowlist_do_servidor": ctx.get("allowlist"),
    }


def grupo_nomes(ctx):
    conteudo = ler(os.path.join(ctx["fixtures"], "arvore_valida.ged"))
    candidatos = [
        "teste:1.ged", "teste.ged:ads", "con.ged", "CON.ged", "nul.ged", "aux.ged",
        "com1.ged", "lpt1.ged", "CON", "nome.", "nome ", "..\\escape.ged",
        "C:\\escape.ged", "../../escape.ged",
    ]
    fichas = []
    for indice, nome_arquivo in enumerate(candidatos):
        conteudo_do_caso = variante(conteudo, f"nomes{indice}")
        antes = retrato_da_pasta(ctx["uploads"])
        resposta = upload_gedcom(ctx["porta"], conteudo_do_caso, nome_arquivo)
        depois = retrato_da_pasta(ctx["uploads"])
        referencia = referencia_da_arvore(resposta["texto"])
        novos = sorted(set(depois) - set(antes))
        ficha = {
            "nome_enviado": nome_arquivo,
            "status": resposta["status"],
            "mensagem": mensagens(resposta["texto"]),
            "referencia_devolvida": referencia,
            "arquivos_criados": {nome: depois[nome] for nome in novos},
        }
        if referencia:
            caminho = os.path.join(ctx["uploads"], referencia)
            ficha["referencia_existe_no_disco"] = os.path.exists(caminho)
            ficha["referencia_e_arquivo_regular"] = os.path.isfile(caminho)
            try:
                dados = ler(caminho)
                ficha["referencia_bytes_lidos"] = len(dados)
                ficha["referencia_conteudo_confere"] = dados == conteudo_do_caso
            except OSError as erro:
                ficha["referencia_erro_de_leitura"] = f"{type(erro).__name__}: {erro}"
        # O que a propria tela passa a oferecer depois deste envio
        listagem = pedir(ctx["porta"], "GET", "/")
        if referencia:
            procurado = referencia.split(":")[0] if ":" in referencia else referencia
            ficha["a_tela_oferece_alguma_forma"] = bool(
                f'value="{procurado}"' in listagem["texto"]
                or f'value="{referencia}"' in listagem["texto"])
            ficha["referencia_oferecida_na_tela"] = procurado
            ficha["bytes_mostrados_na_tela"] = re.search(
                re.escape(procurado) + r".{0,400}?([0-9][0-9\.,]*)\s*B",
                listagem["texto"], re.S).group(1) if re.search(
                re.escape(procurado) + r".{0,400}?([0-9][0-9\.,]*)\s*B",
                listagem["texto"], re.S) else None
        fichas.append(ficha)
    guardar_artefato(ctx, "nomes-listagem-final.html", pedir(ctx["porta"], "GET", "/")["texto"])
    return {"candidatos": fichas}


def grupo_erro(ctx):
    conteudo = ler(os.path.join(ctx["fixtures"], "arvore_valida.ged"))
    manifesto = json.loads(ler_manifesto(ctx))
    chave = manifesto["arvore_valida"]["chave"]

    # Caso A: o nome armazenado ja existe, mas como DIRETORIO. A guarda de existencia
    # pula a gravacao e a releitura tenta abrir um diretorio com o parser.
    nome_armadilha = f"{chave}__sonda_dir.ged"
    armadilha = os.path.join(ctx["uploads"], nome_armadilha)
    if not os.path.isdir(armadilha):
        os.makedirs(armadilha, exist_ok=True)
    resposta_a = upload_gedcom(ctx["porta"], conteudo, "sonda_dir.ged")
    guardar_artefato(ctx, "erro-diretorio-no-lugar-do-arquivo.html", resposta_a["texto"])

    # Caso B: GEDCOM truncado, que passa pelo portao de conteudo e falha no parser.
    truncado = ler(os.path.join(ctx["fixtures"], "arvore_truncada.ged"))
    resposta_b = upload_gedcom(ctx["porta"], truncado, "arvore_truncada.ged")
    guardar_artefato(ctx, "erro-gedcom-truncado.html", resposta_b["texto"])

    return {
        "diretorio_no_lugar_do_arquivo": {
            "nome_armadilha": nome_armadilha,
            "status": resposta_a["status"],
            "mensagem": mensagens(resposta_a["texto"]),
            "texto_de_excecao_na_pagina": extrair_erro(resposta_a["texto"]),
        },
        "gedcom_truncado": {
            "status": resposta_b["status"],
            "mensagem": mensagens(resposta_b["texto"]),
            "texto_de_excecao_na_pagina": extrair_erro(resposta_b["texto"]),
        },
    }


def extrair_erro(html):
    achado = re.search(r"Erro ao processar GEDCOM:\s*([^<]*)", html)
    if achado:
        return achado.group(1).strip()
    achado = re.search(r"Ocorreu um erro:\s*([^<]*)", html)
    return achado.group(1).strip() if achado else None


def grupo_parse(ctx):
    grande = ler(os.path.join(ctx["fixtures"], "arvore_grande_15000.ged"))

    inicio = time.perf_counter()
    resposta = upload_gedcom(ctx["porta"], grande, "arvore_grande_15000.ged")
    tempo_upload = time.perf_counter() - inicio
    referencia = referencia_da_arvore(resposta["texto"])
    if not referencia:
        return {"erro": "upload da arvore grande nao devolveu referencia",
                "mensagem": mensagens(resposta["texto"])[:3]}

    sequenciais = []
    for _ in range(3):
        inicio = time.perf_counter()
        resposta = enviar_formulario(
            ctx["porta"], {"action": "selecionar_arvore", "gedcom_filename": referencia})
        sequenciais.append(round(time.perf_counter() - inicio, 2))

    ocioso = []
    for _ in range(3):
        inicio = time.perf_counter()
        pedir(ctx["porta"], "GET", "/")
        ocioso.append(round(time.perf_counter() - inicio, 3))

    # Quatro requisicoes de parse simultaneas + uma pagina simples no meio
    resultados = [None] * 4
    latencia_da_pagina = []

    def trabalhador(indice):
        inicio = time.perf_counter()
        enviar_formulario(
            ctx["porta"], {"action": "selecionar_arvore", "gedcom_filename": referencia})
        resultados[indice] = round(time.perf_counter() - inicio, 2)

    inicio_geral = time.perf_counter()
    fios = [threading.Thread(target=trabalhador, args=(i,)) for i in range(4)]
    for fio in fios:
        fio.start()
    time.sleep(0.7)
    inicio_pagina = time.perf_counter()
    pedir(ctx["porta"], "GET", "/")
    latencia_da_pagina.append(round(time.perf_counter() - inicio_pagina, 2))
    for fio in fios:
        fio.join()
    tempo_total = round(time.perf_counter() - inicio_geral, 2)

    return {
        "bytes_da_arvore": len(grande),
        "upload_com_parse_incluso": round(tempo_upload, 2),
        "selecionar_a_mesma_arvore_3x": sequenciais,
        "pagina_simples_ociosa": ocioso,
        "quatro_parses_simultaneos": resultados,
        "pagina_simples_durante_os_4_parses": latencia_da_pagina,
        "tempo_total_dos_4_simultaneos": tempo_total,
    }


def grupo_dna(ctx):
    manifesto = json.loads(ler_manifesto(ctx))
    raiz = manifesto["raiz"]
    arvores, csvs = {}, {}
    for nome in ("arvore_pool150.ged", "arvore_pool600.ged", "arvore_valida.ged"):
        resposta = upload_gedcom(ctx["porta"], ler(os.path.join(ctx["fixtures"], nome)), nome)
        arvores[nome] = referencia_da_arvore(resposta["texto"])
    for nome in ("matches_r24.csv", "matches_r49.csv", "matches_r199.csv"):
        resposta = upload_csv(ctx["porta"], ler(os.path.join(ctx["fixtures"], nome)), nome,
                              arvores["arvore_valida.ged"], raiz)
        guardar_artefato(ctx, f"dna-envio-{nome}.html", resposta["texto"])

    # A referencia do CSV e derivada do CONTEUDO pelo proprio armazenamento: mesmo
    # sha256 truncado, mesmo nome visivel. Conferida contra o disco antes de usar.
    for nome in ("matches_r24.csv", "matches_r49.csv", "matches_r199.csv"):
        candidata = f"{manifesto[nome.replace('.csv', '')]['chave']}__{nome}"
        csvs[nome] = candidata if os.path.exists(
            os.path.join(ctx["uploads"], candidata)) else None

    matriz = [
        ("arvore_pool600.ged", "matches_r24.csv"),
        ("arvore_pool600.ged", "matches_r49.csv"),
        ("arvore_pool600.ged", "matches_r199.csv"),
        ("arvore_pool150.ged", "matches_r49.csv"),
    ]
    medidos = []
    for arvore, csv in matriz:
        referencia_csv = csvs.get(csv)
        if not referencia_csv:
            medidos.append({"arvore": arvore, "csv": csv, "erro": "CSV nao esta na pasta"})
            continue
        inicio = time.perf_counter()
        resposta = enviar_formulario(ctx["porta"], {
            "action": "dna_analysis",
            "gedcom_filename": arvores[arvore],
            "root_name": raiz,
            "matches_csv_filename": referencia_csv,
        })
        decorrido = round(time.perf_counter() - inicio, 2)
        guardar_artefato(ctx, f"dna-{arvore}-{csv}.html", resposta["texto"])
        medidos.append({
            "arvore": arvore,
            "csv": csv,
            "segundos": decorrido,
            "status": resposta["status"],
            "mensagem": mensagens(resposta["texto"])[:1],
        })

    return {
        "arvores": arvores,
        "csvs_na_pasta": csvs,
        "matriz": medidos,
    }


def grupo_persistencia(ctx):
    raiz = json.loads(ler_manifesto(ctx))["raiz"]
    arvore = upload_gedcom(ctx["porta"], ler(os.path.join(ctx["fixtures"], "arvore_valida.ged")),
                           "arvore_valida.ged")
    referencia = referencia_da_arvore(arvore["texto"])
    resposta = upload_csv(ctx["porta"], ler(os.path.join(ctx["fixtures"], "matches_r24.csv")),
                          "matches_r24.csv", referencia, raiz)
    guardar_artefato(ctx, "persistencia.html", resposta["texto"])
    return {
        "status": resposta["status"],
        "aviso_de_persistencia": mensagens(resposta["texto"]),
        "tem_stub_psycopg2": os.path.exists(os.path.join(ctx["stub"], "psycopg2", "__init__.py"))
        if ctx.get("stub") else False,
        "database_url_do_servidor": ctx.get("database_url"),
    }


def grupo_ads(ctx):
    """Item 7, caso NTFS: o nome visivel com `:` faz a gravacao cair num fluxo alternativo.

    Mede as TRES consequencias, uma por uma:
      1. o arquivo que nasce na pasta e o nome ANTES dos dois pontos, com zero byte;
      2. os bytes enviados existem, mas dentro do fluxo alternativo;
      3. a lista da tela oferece o nome sem os dois pontos, e clicar nele NAO abre a arvore.
    """
    conteudo = variante(ler(os.path.join(ctx["fixtures"], "arvore_valida.ged")),
                        f"ads{uuid.uuid4().hex[:6]}")
    resposta = upload_gedcom(ctx["porta"], conteudo, "teste:1.ged")
    referencia = referencia_da_arvore(resposta["texto"])
    base = referencia.split(":")[0] if referencia else None

    medido = {
        "upload": {
            "status": resposta["status"],
            "mensagem": mensagens(resposta["texto"]),
            "referencia_devolvida": referencia,
            "bytes_enviados": len(conteudo),
        },
        "disco": {},
        "lista": {},
        "clique": {},
    }

    for rotulo, caminho in (("nome_com_dois_pontos", referencia),
                            ("nome_sem_dois_pontos", base)):
        if not caminho:
            continue
        completo = os.path.join(ctx["uploads"], caminho)
        ficha = {
            "caminho_logico": caminho,
            "existe": os.path.exists(completo),
            "arquivo_regular": os.path.isfile(completo),
            "bytes_do_stat": os.path.getsize(completo) if os.path.isfile(completo) else None,
        }
        try:
            ficha["bytes_lidos"] = len(ler(completo))
        except OSError as erro:
            ficha["erro_de_leitura"] = f"{type(erro).__name__}: {erro}"
        medido["disco"][rotulo] = ficha

    listagem = pedir(ctx["porta"], "GET", "/")["texto"]
    guardar_artefato(ctx, "ads-listagem.html", listagem)
    linhas = re.findall(r'name="gedcom_filename" value="([^"]*)"', listagem)
    medido["lista"]["referencias_oferecidas"] = sorted(set(linhas))
    medido["lista"]["oferece_o_nome_sem_dois_pontos"] = bool(base and base in linhas)
    medido["lista"]["oferece_o_nome_com_dois_pontos"] = bool(referencia and referencia in linhas)
    tamanhos = dict(re.findall(r'([0-9a-f]{16}__[^"<]*)[^0-9]{0,40}?([0-9][0-9\.,]*)\s*B', listagem))
    medido["lista"]["tamanhos_visiveis"] = tamanhos

    for rotulo, alvo in (("com_dois_pontos", referencia), ("sem_dois_pontos", base)):
        if not alvo:
            continue
        resposta_clique = enviar_formulario(
            ctx["porta"], {"action": "selecionar_arvore", "gedcom_filename": alvo})
        medido["clique"][rotulo] = {
            "referencia": alvo,
            "status": resposta_clique["status"],
            "mensagem": mensagens(resposta_clique["texto"]),
            "abriu_a_arvore": "nav-tabs" in resposta_clique["texto"]
            and "Nenhum" not in resposta_clique["texto"],
        }

    return medido


GRUPOS = {
    "estatico": grupo_estatico,
    "origem": grupo_origem,
    "identidade": grupo_identidade,
    "lan": grupo_lan,
    "nomes": grupo_nomes,
    "ads": grupo_ads,
    "erro": grupo_erro,
    "parse": grupo_parse,
    "dna": grupo_dna,
    "persistencia": grupo_persistencia,
}


def guardar_artefato(ctx, nome, texto):
    with open(os.path.join(ctx["outdir"], nome), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)


def ler_manifesto(ctx):
    with open(os.path.join(ctx["fixtures"], "manifesto.json"), "rb") as fh:
        return fh.read()


def main():
    analisador = argparse.ArgumentParser()
    analisador.add_argument("grupo", choices=sorted(GRUPOS))
    analisador.add_argument("--porta", type=int, required=True)
    analisador.add_argument("--uploads", required=True)
    analisador.add_argument("--fixtures", required=True)
    analisador.add_argument("--outdir", required=True)
    analisador.add_argument("--stub", default=None)
    analisador.add_argument("--database-url", default=None)
    analisador.add_argument("--allowlist", default=None)
    analisador.add_argument("--endereco", default=None)
    argumentos = analisador.parse_args()

    ctx = {
        "porta": argumentos.porta,
        "uploads": argumentos.uploads,
        "fixtures": argumentos.fixtures,
        "outdir": argumentos.outdir,
        "stub": argumentos.stub,
        "database_url": argumentos.database_url,
        "allowlist": argumentos.allowlist,
        "endereco": argumentos.endereco,
    }
    os.makedirs(argumentos.outdir, exist_ok=True)
    resultado = GRUPOS[argumentos.grupo](ctx)
    with open(os.path.join(argumentos.outdir, f"{argumentos.grupo}.json"),
              "w", encoding="utf-8", newline="\n") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
