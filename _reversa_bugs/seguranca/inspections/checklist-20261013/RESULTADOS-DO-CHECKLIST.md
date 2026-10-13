# Checklist de Validacao da Auditoria de Seguranca: resultado da execucao

**Projeto:** reversa_analisador_genealogico
**Ponto de partida:** `checklist-auditoria-reversa-analisador-genealogico.md` (9 itens) derivado do run-1 do `/security-audit`
**Commit medido:** `c670788a75fdcfda755b001e52b14f2b045bb617` (o mesmo conteudo revisado no run-1)
**Data da medicao:** sessao corrente
**Ambiente:** Windows, 4 processadores logicos, Python 3.14.6 do `.venv/` do repositorio, Flask 3.1.3 servido por waitress 3.0.2 com 4 threads

## O que este documento e

O run-1 levantou 9 leads por **leitura de codigo**, sem executar nada. Este documento
registra o que aconteceu quando os 9 foram **medidos**: o app foi subido de verdade, em
loopback, e sondado por HTTP. Cada item abaixo diz o numero medido, o comando que o
produziu e o que **nao** foi medido.

Nada aqui e estimativa apresentada como medicao. Onde a conclusao depende de
comportamento do navegador ou de um driver ausente, esta escrito **inferido**.

## Garantias do procedimento (dados e isolamento)

- **Zero dado real.** Arvores, pessoas e CSVs foram gerados por
  `_sondas-seguranca/gerar_fixtures.py`. O `.env`, a `src/uploads/` real e os arquivos do
  operador nunca foram lidos nem escritos.
- **Pasta de upload desviada** para o scratch (`ANALISADOR_UPLOAD_FOLDER` em diretorio
  temporario). Nenhum byte foi gravado em `src/uploads/`.
- **Somente loopback.** As instancias escutaram em `127.0.0.1` e em `127.0.0.2` (segundo
  endereco de loopback). A maquina **nao** foi exposta na rede local para medir o allowlist.
- **Legado intocado.** Nenhum arquivo pre-existente do projeto foi criado, alterado ou
  apagado. O unico caminho novo e `_reversa_bugs/_sondas-seguranca/`.
- Cada instancia foi encerrada ao fim do seu grupo de sondas.

## Quadro final

| # | Item | Status depois da medicao |
|---|------|--------------------------|
| 1 | `POST /` sem verificacao de origem (CSRF) | **CONFIRMADO** (medido no HTTP) |
| 2 | Sem autenticacao ou autorizacao | **CONFIRMADO como postura declarada**, com o limite do modo LAN medido |
| 3 | Arvore reprocessada a cada requisicao | **CONFIRMADO**, com agravante novo medido (colapso de concorrencia) |
| 4 | Analise de DNA sem limite de linhas ou pool | **CONFIRMADO** (custo cresce com linhas x pool; nenhum teto) |
| 5 | Scripts de terceiros sem SRI nem CSP | **CONFIRMADO** |
| 6 | Pagina sem protecao contra clickjacking | **CONFIRMADO** (ausencia dos dois controles medida) |
| 7 | Nome de arquivo do cliente sem checagem de arquivo regular | **PARCIAL: nomes reservados do Windows REFUTADOS; o `:` CONFIRMADO como defeito** |
| 8 | Mensagens de erro expoem texto de excecao cru | **CONFIRMADO**, inclusive com o caminho absoluto do servidor |
| 9 | Erro do driver do banco exposto na pagina | **CONFIRMADO por mecanismo** (driver real ausente; medido com duble e sem duble) |

---

## 1. `POST /` sem verificacao de origem

**Medido.** Envio de GEDCOM sintetico com `Origin: http://atacante.exemplo` e
`Referer: http://atacante.exemplo/pagina-hostil.html`: **200**, arquivo gravado,
mensagem de sucesso. A acao destrutiva `aposentar_arquivo` com os mesmos cabecalhos
hostis: **200**, arquivo movido para `_aposentados/` (709 bytes, intacto). Repetido sem
`Origin` nem `Referer`: mesmo resultado. Nenhum campo de token existe em nenhum
formulario da pagina (`tem_campo_de_token: false`), e nenhum cookie e emitido, entao nao
ha nada a que um token possa ser amarrado.

**Numeros:** `evidencias/origem.json`, `evidencias/estatico.json`.

**Nuance importante, tambem medida.** O `TRUSTED_HOSTS` **nao** fecha este vetor: uma
requisicao com `Host: 127.0.0.1:5099` e `Origin` hostil e aceita. O que a lista de hosts
fecha e o DNS rebinding (Host com o dominio do atacante, medido como **400**), nao o
CSRF de uma pagina que endereca `127.0.0.1` diretamente.

**Inferido.** A exploracao por navegador depende do navegador do operador (o pedido
cruzado e um POST de formulario, sem preflight) e de a aplicacao estar no ar no momento
em que a pagina hostil for aberta. Nao houve teste com navegador real.

**Gravidade:** alta no modo exposto (a acao destrutiva e a de aposentar, e o upload
aceita conteudo escolhido pelo atacante); menor no loopback, onde o atacante ainda
precisa do navegador do operador.

## 2. Sem autenticacao ou autorizacao

**Medido.** `GET /` sem nenhuma credencial: **200**, 28.858 bytes, com a lista de
arquivos; `Set-Cookie` ausente; `WWW-Authenticate` ausente; nenhuma pagina de login
existe. `Host: atacante.exemplo`: **400** ("Host 'atacante.exemplo' is not trusted.").

**Medido no modo LAN.** Instancia escutando em `127.0.0.2` (fora da lista padrao) sem a
variavel: **400** em todas as requisicoes, mesmo com o listener no ar. Com
`ANALISADOR_HOSTS_PERMITIDOS=127.0.0.2`: **200** e 63.657 bytes de pagina completa para
um cliente que **nao apresentou credencial nenhuma**. Ou seja: o allowlist e o unico
controle de borda, e ele e opt-in por nome.

**Numeros:** `evidencias/identidade.json`, `evidencias/lan-sem-allowlist.json`, `evidencias/lan-com-allowlist.json`.

**Veredito.** Nao e defeito novo: a ausencia de identidade e decisao declarada
(`src/app.py:52-76`, `RN-06`, ADR-26, dividas #3 e #4). O que a medicao acrescenta e o
numero do modo LAN: **quem alcanca a porta, com o allowlist preenchido, tem o inventario
completo e a acao destrutiva**. O `docker-compose.yml` nao expoe por padrao
(`ANALISADOR_HOST: "0.0.0.0"` dentro do container, `ports: "127.0.0.1:5080:5000"` no
host), entao o padrao do projeto continua fechado.

## 3. Arvore reprocessada do zero a cada requisicao, sem cache e sem prazo

**Medido.** Arvore sintetica de 15.000 pessoas, 1.303.670 bytes.

| Medicao | Resultado |
|---|---|
| Upload com parse incluso | 6,26 s |
| Selecionar a mesma arvore, 3 vezes seguidas | 5,54 s / 4,33 s / 4,24 s |
| Linha de base depois, mesma arvore | 12,23 s / 6,88 s / 10,28 s |
| Arvore pequena (8 pessoas), mesma rota | 0,031 s / 0,014 s / 0,020 s |
| `GET /` ocioso | 0,004 s a 0,015 s |

As tres selecoes seguidas custam o **preco inteiro** cada uma: **nao ha cache entre
requisicoes**, medido, nao inferido. O custo da rota com a arvore pequena mostra que o
que domina e o reprocessamento do arquivo, e nao a rota.

**Agravante novo (nao estava no run-1): o processo inteiro para.**

| Requisicoes simultaneas na mesma arvore | Tempo de cada uma | `GET /` disparado no meio |
|---|---|---|
| 1 | 12,34 s | 0,05 s |
| 2 | 29,26 s e 28,90 s | 0,06 s |
| 4 | 72,16 s / 71,27 s / 70,31 s / 70,32 s | **69,67 s** |

Com as 4 threads do waitress ocupadas por parses, **uma pagina simples espera 69,67 s**.
Nao e so "a requisicao demora": e a aplicacao inteira parar enquanto a arvore grande e
reprocessada. A variancia da linha de base (4,24 s a 12,34 s para a mesma arvore) tambem
foi registrada: o numero depende do estado da maquina, e por isso a conclusao se apoia na
**relacao** entre as medidas, nao num valor absoluto.

**Numeros:** `evidencias/parse.json`, `evidencias/concorrencia-1.json`, `evidencias/concorrencia-2.json`,
`evidencias/linha_de_base` (saida no console da sessao).

**Causa (inferida).** Parse CPU-bound em processo unico com GIL: `selecionar_arvore` e
`dna_analysis` chamam `_CARREGADOR.carregar` a cada requisicao (`src/app.py:307`), sem
cache de arvore e sem prazo. O projeto ja registrava 20,9 s para a arvore real do
operador (`_reversa_sdd/gaps.md:65`); o que faltava era o efeito da concorrencia.

## 4. Analise de DNA sem limite de linhas nem de pool

**Medido por HTTP** (mesma arvore, CSVs com 24, 49 e 199 linhas alem da linha da raiz):

| Arvore | Pessoas no pool "Silva" | Linhas de fan-out no CSV | Tempo |
|---|---|---|---|
| pool600 | 608 | 24 | 1,22 s |
| pool600 | 608 | 49 | 1,22 s |
| pool600 | 608 | 199 | 3,27 s |
| pool150 | 158 | 49 | 0,33 s |

**Medido no nucleo** (calibracao local, `calibrar.py`): pool600 com 24 linhas = 1,14 s;
pool600 com 199 linhas = 4,94 s; pool150 com 49 linhas = 0,59 s; pool600 com 49 linhas =
0,86 s. Custo marginal de aproximadamente **21,7 ms por linha** com pool de 608 pessoas e
**0,6 ms por pessoa do pool por rodada de 49 linhas**: o produto (linhas) x (pool) e o
driver, e **nao existe teto nem de linhas nem de pool** (199 de 199 linhas foram
processadas, todas descartadas por score, e a analise terminou com 200 resultados
avaliados). Corresponde a `match_candidates` (`src/core/matching.py:86-108`): tres
`fuzz` por candidato do pool, uma vez por linha do CSV, sem limite.

**Numeros:** `evidencias/dna.json`.

**Gravidade:** media. Nao derruba nada sozinho, mas compoe com o item 3: um CSV grande
contra a arvore real (35.460 pessoas) mantem uma thread ocupada por minutos, e com 4
threads o item 3 ja mostrou o que acontece com a quinta requisicao.

## 5. Scripts de terceiros sem integridade (SRI) nem CSP

**Medido** em `GET /` (resposta real, `evidencias/estatico-get-index.html`):

- `<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js">`: **sem** `integrity`, **sem** `crossorigin`
- `<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js">`: **sem** `integrity`, **sem** `crossorigin`
- `Content-Security-Policy`: **ausente** (junto de `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`: todos
  ausentes). Os unicos cabecalhos da resposta sao `content-length`, `content-type`,
  `date` e `server: waitress`.
- Tambem vem de CDN sem integridade: a folha do Bootstrap, as fontes do Google
  (`fonts.googleapis.com`, `fonts.gstatic.com`).

**Consequencia (inferida, comportamento documentado de navegador):** o codigo executado
na origem da aplicacao e o que o CDN entregar no momento da carga; nao ha segundo
mecanismo (CSP) que limite o que um script comprometido poderia fazer.

## 6. Pagina sem protecao contra clickjacking

**Medido.** Nenhum `X-Frame-Options` e nenhum `Content-Security-Policy` com
`frame-ancestors` em nenhuma resposta de `GET /`. A pagina que contem o formulario do
botao destrutivo ("Apagar", `src/templates/index.html:68-73`, com `onsubmit` de
`confirm`) e servida sem nenhum controle de enquadramento.

**Inferido.** Que um navegador carregue a pagina dentro de um `<iframe>` de outro site e
o comportamento padrao sem esses cabecalhos; nao houve teste com navegador real, e o
`confirm()` do proprio botao reduz o risco de um clique unico acidental.

## 7. Nome de arquivo do cliente sem checagem de arquivo regular

Este item se divide em dois, e a medicao separou os dois.

### 7a. Nomes reservados do Windows: REFUTADO

Enviados como nome de arquivo, todos viraram **arquivo regular, legivel, com o conteudo
inteiro e alcancavel pela tela**: `con.ged`, `CON.ged`, `nul.ged`, `aux.ged`, `com1.ged`,
`lpt1.ged` e `CON` (sem extensao). A razao e estrutural: o nome armazenado e
`<16 hexadecimais>__<nome visivel>` (`src/utils/validate.py:99-101`), e o prefixo tira o
nome do espaco de nomes de dispositivo do Windows. Nenhum "sucesso fantasma".

### 7b. Dois pontos (`:`): CONFIRMADO, e o efeito e pior do que o previsto

**Medido com `teste:1.ged`** (709 bytes de GEDCOM valido): a tela responde
**"Arquivo 'teste:1.ged' carregado!"**. No disco nasce **um** arquivo,
`bee820c034ef143d__teste`, com **0 byte**; os 709 bytes enviados vao para o **fluxo
alternativo NTFS** `:1.ged`. A lista da tela nao oferece o nome devolvido
(`...__teste:1.ged`) nem o nome do arquivo que existe (`...__teste`, sem extensao
reconhecida): **a arvore enviada nao aparece em nenhuma das duas abas**. O clique com a
referencia da propria resposta funciona (lendo o fluxo), mas essa referencia so existe
naquela resposta.

**Medido com `teste.ged:ads`**: mesmo mecanismo, mas o arquivo base termina em `.ged`,
entao **a lista oferece** `...__teste.ged` com **0 byte**; clicar nele responde
"Erro: o arquivo 'teste.ged' nao pode ser lido como GEDCOM". A entrada fantasma existe e
nao abre.

**Medido com `C:\escape.ged`** (que chega ao servidor como `C:escape.ged`): o nome
armazenado nao e alcancavel pelo proprio resolvedor (`os.path.basename("C:escape.ged")`
devolve `escape.ged`), entao a tela mostra
**"Erro ao processar GEDCOM: a arvore recem-gravada nao pode ser relida"** e **deixa para
tras um arquivo orfao de 0 byte** (`993a6adffa751f16__C`), com os bytes no fluxo.

**Numeros:** `evidencias/nomes.json`, `evidencias/ads.json`.

**Veredito.** A sanitizacao cobre separadores, acento e espaco, mas nao `:`, e `:` e
separador de fluxo no NTFS. O resultado medido e perda silenciosa de alcance: o operador
le "carregado!" e a arvore nao existe para a interface. E independe de ma-fe: um
`nome:versao.ged` vindo de qualquer exportador reproduz o defeito.

### 7c. Escape de pasta: REFUTADO

`../../escape.ged` gravou `97d11d7e434252a7___.._escape.ged` dentro da pasta (regular,
709 bytes, alcancavel); `..\escape.ged` gravou `...__escape.ged`. Nenhum caminho saiu da
pasta de upload em nenhum dos 14 nomes testados.

## 8. Texto de excecao cru na pagina

**Medido, com o caminho absoluto do servidor.** Com um diretorio ocupando o nome
armazenado esperado, a resposta 200 traz na pagina:

```
Erro ao processar GEDCOM: [Errno 13] Permission denied:
'C:\Users\venda\AppData\Local\Temp\dsh-cvAZP4\reversa-chec-seg\uploads\7b682362af68f7c0__sonda_dir.ged'
```

Isto e `src/app.py:538`, o `except Exception as e` que interpola `{e}` na mensagem. O
nome de usuario do sistema, o caminho da pasta de upload e o errno cru do sistema
operacional saem no HTML da resposta.

**Numeros:** `evidencias/erro.json`, `evidencias/erro-diretorio-no-lugar-do-arquivo.html`.

**Nao reproduzido:** o GEDCOM truncado (`0 HEAD` sem `TRLR`) **nao** entrou no
`except`: o `ged4py` aceitou o arquivo e a tela disse "carregado!". O mesmo padrao
`f"... {e}"` existe em `src/app.py:680` (DNA) e `:710` (busca de caminho); medido o
mecanismo em um dos tres, os outros dois sao o mesmo texto de codigo.

## 9. Erro do driver do banco exposto na pagina

**Medido, dois casos.**

1. **Driver ausente (estado real do `.venv/`):** com `DATABASE_URL` definida, a pagina da
   analise mostra `Historico nao registrado: o driver do banco nao esta instalado neste
   interpretador (No module named 'psycopg2').` O `psycopg2-binary` esta pinado no
   `requirements.txt` e **nao esta instalado** no interpretador do repositorio (achado
   L-26 do proprio projeto), confirmado por `import psycopg2` falhando.
2. **Driver presente e banco recusando (duble sintetico):** com um duble de `psycopg2`
   no `PYTHONPATH` (`_sondas-seguranca/stub/psycopg2/`), a pagina mostra
   `Historico nao registrado: OperationalError: connection to server at "127.0.0.1", port
   5432 failed: FATAL: password authentication failed for user "analisador-sonda"`.

O texto do caso 2 e do duble (usuario, senha, host e base **inventados**): o driver real
nao esta instalado, entao o caso "driver real" nao pode ser executado neste ambiente. O
que a sonda mede e o que a **aplicacao** faz com o texto: `src/ports/adaptadores.py:311`
interpola `type(erro).__name__` e o `str` da excecao dentro do aviso que o template
renderiza (`src/templates/index.html:401-403`). Com o driver real, o texto seria o do
driver, que e exatamente o formato medido.

**Numeros:** `evidencias/persistencia-sem-driver/persistencia.json` (caso 1) e
`evidencias/persistencia-com-duble/persistencia.json` (caso 2).

---

## Achados que nao estavam no checklist

1. **Colapso de concorrencia do item 3:** 4 selecoes simultaneas custam ~70 s cada e
   bloqueiam uma pagina simples por 69,67 s. O run-1 falava de custo por requisicao; o
   efeito medido e de indisponibilidade do processo inteiro.
2. **`C:\...` como nome de arquivo:** erro opaco ("a arvore recem-gravada nao pode ser
   relida") **e** arquivo orfao de 0 byte na pasta, com os bytes no fluxo alternativo.
3. **A referencia devolvida no sucesso pode nao ser a que a lista oferece** (caso
   `teste:1.ged`): o contrato de continuidade entre requisicoes depende de o operador
   usar a resposta imediatamente.
4. **Variancia da linha de base:** a mesma arvore levou de 4,24 s a 12,34 s em medicoes
   proximas. Qualquer orcamento de tempo para o item 3 precisa de margem.

## Limites desta validacao (o que NAO foi medido)

- **Navegador real:** nenhum teste de iframe, de SRI violado, de POST cross-site efetivo
  ou de Private Network Access. O que foi medido e a resposta HTTP do servidor.
- **Postgres real:** o driver nao esta no `.venv/`; o caso "driver real" usou duble.
- **Outro dispositivo fisico:** a interface "de fora" foi simulada com `127.0.0.2`. O que
  se mediu foi a decisao do allowlist, nao a topologia.
- **Os 5 candidatos ja descartados no run-1** nao foram revalidados, conforme o proprio
  checklist manda.
- **Sem sandbox de SO nesta sessao:** o app foi executado com o interpretador do
  repositorio, com a pasta de upload desviada e dados sinteticos, mas sem confinamento de
  rede, CPU ou memoria imposto pelo ambiente.

## Reprodutibilidade

```
gerar_fixtures.py <scratch>/fixtures        # fixtures sinteticas + manifesto com chaves
# subir a instancia (env: ANALISADOR_UPLOAD_FOLDER, ANALISADOR_PORT, ANALISADOR_HOST, ANALISADOR_THREADS)
sondas_http.py <grupo> --porta <p> --uploads <u> --fixtures <f> --outdir <o>
concorrencia.py <n> --porta <p> --fixtures <f> --referencia <nome armazenado>
linha_de_base.py --porta <p> --pequena <ref> --grande <ref>
calibrar.py <fixtures>                      # mede o nucleo sem HTTP
```

Grupos de `sondas_http.py`: `estatico`, `origem`, `identidade`, `lan`, `nomes`, `ads`,
`erro`, `parse`, `dna`, `persistencia`. Os HTMLs crus de cada resposta ficam em
`<outdir>` e os JSONs de resultado tambem.

---

## Desfecho no registro (Reversa)

Os 6 defeitos medidos foram registrados pelo `/reversa-debugger` no contexto novo
`_reversa_bugs/seguranca/`, com um bug por defeito distinto:

| # | ID | Defeito | Severidade | Visibilidade |
|---|---|---|---|---|
| 7 | `BUG-20261013-2EFQ` | Nome com `:` grava em fluxo alternativo NTFS e torna a arvore inalcancavel | high / P1 | `normal` |
| 8 | `BUG-20261013-WREC` | Texto de excecao cru, com o caminho absoluto do servidor | high / P1 | `restricted` |
| 9 | `BUG-20261013-GTAY` | Texto do driver do banco na pagina | medium / P2 | `restricted` |
| 10 | `BUG-20261013-Z5BC` | `POST` de estado sem verificacao de origem nem token | medium / P2 | `restricted` |
| 11 | `BUG-20261013-4PYJ` | Scripts de CDN sem `integrity` e ausencia de CSP | medium / P2 | `restricted` |
| 12 | `BUG-20261013-X7EN` | Resposta sem protecao de enquadramento | medium / P2 | `restricted` |

Registrado tambem:

- intake: `_reversa_bugs/seguranca/intake/relato-20261013-1305.md`, com o checklist recebido
  copiado ao lado;
- views do contexto: `_reversa_bugs/seguranca/generated/` (geradas com 0 inconsistencias de
  invariante) e o espelho `_reversa_sdd/traceability/bugs.md`;
- o gerador das views, para reprodutibilidade: `_reversa_bugs/_ferramentas/gerar_views.py`.

**Efeito da visibilidade nas views.** Pelo contrato do registro, bug com
`visibility: restricted` fica fora das views e do espelho. Como 5 dos 6 foram classificados
assim, o `generated/graph.html` deste contexto mostra **um** bug (o 2EFQ); os outros cinco
aparecem no `index.md` apenas como identificador e a palavra "restrito". O registro completo
de cada um, com a reproducao passo a passo, esta no `bug.md` da respectiva pasta. Se o
operador quiser ve-los nas views, a mudanca de `visibility` para `normal` nos cinco arquivos
e decisao humana, e depois basta regerar:

```
python _reversa_bugs/_ferramentas/gerar_views.py --contexto seguranca
```

**Dois dos seis sao comportamento declarado**, e os registros dizem isso por escrito:

- `BUG-20261013-WREC`: o literal `Erro ao processar GEDCOM: {e}` e contrato congelado nos
  tres contratos de unidade, e o adendo `014-endurecimento-da-borda` ja registra o vazamento
  como comportamento aceito, na divida `E-01`. O bug guarda a **ocorrencia medida** (caminho
  absoluto e nome de usuario no corpo da resposta) e a consequencia de seguranca que aquela
  decisao nao avaliou; fechar exige adendo que revogue o literal.
- `BUG-20261013-GTAY`: o formato `Historico nao registrado: {Tipo}: {msg}` tambem e literal
  prescrito (`analise-dna/contracts.md`), e o conteudo do `{msg}` nunca foi objeto de decisao.
