# Adendo 011: Escolher arquivo da lista

> Vigente desde 2026-10-09.
> Feature: `_reversa_forward/011-escolher-arquivo-da-lista/`
> Convergido por `/reversa-sync` (`T032`).

## 1. O que esta feature muda na spec efetiva

Esta e a **primeira feature que altera a tela de entrada desde a reconstrucao do legado**, e ela muda
tres contratos ao mesmo tempo. O nucleo nao e tocado.

| Artefato | Secao | Tipo de impacto | O que muda |
|---|---|---|---|
| `upload-gedcom/contracts.md` | §2.1 (nome armazenado) | `delta-de-dados` | **Nada muda no formato.** A feature passa a **ler** a pasta que ja existia, e o nome continua `<16 hex>__<nome visivel>` |
| `analise-dna/contracts.md` | §1 (requisicao da analise) | `delta-de-contrato-externo` | A analise passa a aceitar o CSV por **referencia** (`matches_csv_filename`), alem do arquivo. O campo de arquivo **permanece**, e a referencia tem **precedencia** |
| `openapi/index.yaml` | `RequisicaoAnaliseDna` (linhas 164-186) | `delta-de-contrato-externo` | `matches_csv` deixa de ser **sempre** obrigatorio: a pre-condicao vira disjuncao. O `required` da linha 167 passa a ser condicional |
| `_reversa_sdd/domain.md` | §4, linha de `action=dna_analysis` | `regra-alterada` | A pre-condicao 🟢 **"CSV presente"** passa a **"CSV presente ou referencia presente"**. A leitura literal da linha deixa de valer |
| `_reversa_sdd/architecture.md` | §7, divida 8 (estado entre requisicoes) | `regra-removida` | **Nada e removido.** Esta linha existe para declarar que a divida **continua aberta** e que a feature nao a fechou: a escolha do operador nao sobrevive ao fechamento da pagina |
| `src/templates/index.html` | ramo `{% if not gedcom_filename %}` | `componente-extinto` | O **estado inicial de envio obrigatorio** deixa de existir: o `GET /` entrega as duas abas com as listas, e o envio se muda para dentro da aba |
| `interfaces/formulario-http.md` · `openapi/index.yaml` | contrato do formulario | `delta-de-contrato-externo` | **Quarta `action`**: `selecionar_arvore`, com `gedcom_filename` no `form`. Acrescentada em 2026-10-09, depois de medida a tela: a lista era **texto puro** e nao havia como escolher arvore nenhuma. O `RN-08` passa a falar de quatro `action`, e nenhum campo existente mudou |
| `_reversa_sdd/screens/golden/SCR-001` | golden da tela inicial | `delta-de-dados` | **Nao e recapturado.** Ele captura o **oraculo legado congelado**, e um oraculo congelado nao deixa de valer porque o candidato mudou. O que existe e divergencia declarada |

## 2. O que NAO muda, e por que isso importa

- **O nucleo.** `src/core/`, `src/parsers/` e `src/application/` com `git diff --stat` **vazio** (`T026`).
- **Os goldens.** `git status` do diretorio vazio, sha256 `ec07f71b4084269a` (`T027`).
- **O instrumento de paridade.** `harness.py` byte a byte igual, e a **paridade continua 100 %** (`T024`).
  A premissa de que ele e insensivel ao template foi lida no codigo na investigacao e **medida por
  execucao** nesta rodada.
- **A pasta de uploads.** Nenhuma acao da feature escreve nela: o conjunto de `sha256` e **identico**
  antes e depois de percorrer todas as telas (`T025`, `RF-08`).
- **As tres `action`.** `upload_gedcom`, `path_search` e `dna_analysis` mantem nome e campos (`RN-08`).

## 3. Regras novas que a feature cria

| Regra | Enunciado | Origem |
|---|---|---|
| `RN-03` | A aba de arvore lista o nome visivel que termina em `.ged`; a de DNA, `.csv` | requisito |
| `RN-09` | A lista seleciona por extensao do nome visivel, **sem ler conteudo**; a recusa acontece no uso | decisao da §9 |
| `RN-10` | Arquivo **sem chave** no nome vira item proprio, marcado | decisao da §9 |
| `RN-11` | Item cujo arquivo **nao pode ser usado por referencia** e exibido com a marca de indisponivel e o motivo, e **continua na lista** | **auditoria de 2026-10-09**, apos medir 7 de 19 arquivos inalcancaveis |
| `RN-12` | O item da lista de arvores e um **controle submetivel** (`action=selecionar_arvore`); o item indisponivel continua listado e **nao** ganha botao de escolha | **medicao no navegador em 2026-10-09**: a lista era texto puro, sem `select`, radio, link ou formulario, e o `RF-02` nao estava satisfeito |
| `RN-13` | O rotulo exibido sai **sem a ultima extensao** e com os **simbolos trocados por espaco** (`Backup-Arvore-Sandro-12-11-2024.ged` → `Backup Arvore Sandro 12 11 2024`). A particao por aba, a marca de indisponivel e a referencia enviada ao formulario continuam lendo o nome visivel **cru** | **pedido do operador em 2026-10-09** |
| `RN-14` | O botao **"Apagar" aposenta**, e nao apaga: o arquivo sai da lista e continua inteiro no disco, em `<pasta>/_aposentados/`. A referencia aceita e um **nome simples**, e nao a forma canonica com chave — os arquivos sem chave sao justamente os que o operador mais quer tirar da lista. O botao verde **"Abrir"** e o `selecionar_arvore` de sempre, com rotulo e cor novos | **pedido do operador em 2026-10-10** |
| `RN-15` | A lista das duas abas e uma **tabela com colunas**: `Nome`, `Situacao`, `Arquivos`, `Tamanho`, `Enviado em`, `Gerenciar`. A contagem do grupo deixa de ser badge condicional e vira coluna (`RN-01`); a marca de indisponivel vira coluna com o visto verde ou o motivo escrito (`RN-11`). A coluna **"Numero" da tela de referencia NAO existe**: nao ha identificador publico de arvore, e a chave de conteudo nao pode ocupar esse lugar (`D-09`). A tabela vive **dentro** do ramo da lista, para a tela sem arquivo nenhum ficar byte a byte igual | **pedido do operador em 2026-10-10** |
| `RN-16` | O titulo do topo deixa de ser texto e passa a ser a **arte enviada pelo operador**, servida por `GET /banner.png`. O `<h1>` **permanece**, envolvendo a imagem, e o texto sai da tela visivel para o `alt` — a tela nao perde o titulo de nivel 1 nem o que um leitor de tela anuncia. A arte servida e uma **renderizacao derivada**, e nao o arquivo enviado: ele chegou sem canal alfa, com o quadriculado de transparencia gravado no bitmap. Arte ausente devolve `404` e a tela continua de pe | **pedido do operador em 2026-10-10** |
| `RN-17` | O reenvio de um arquivo tem **tres desfechos distintos**, e nao mais uma resposta unica: **identico** (mesmo nome e mesmo conteudo) avisa que ja estava armazenado e nao grava nada; **atualizado** (mesmo nome, conteudo diferente) **substitui** — a versao anterior e **aposentada** para `<pasta>/_aposentados/`, nunca apagada (`RN-07`), e a lista fica com uma linha; **novo** mantem o literal congelado `Arquivo '...' carregado!`. A identidade do "mesmo arquivo" e o **nome visivel completo**, como o operador o escreveu — um `arvore.csv` **nao** e substituido por um envio de `arvore.ged` | **pedido do operador em 2026-10-10** |
| `RN-18` | O conteudo recusado tem **uma frase fixa**: `Arquivo nao reconhecido como GEDCOM. Favor, enviar o arquivo correto.` O motivo tecnico do validador (`arquivo vazio`, `conteudo binario`, `nao comeca com a declaracao 0 HEAD`) **nao vai para a tela**. Custo declarado: as tres recusas passam a ter o mesmo texto, e o operador perde a pista de qual foi. O motivo **nao se perdeu** — continua dentro de `GedcomNaoSuportado`, que o carrega desde a feature 006 (`A002`); so a apresentacao deixou de exibi-lo | **pedido do operador em 2026-10-10** |
| `RN-19` | A tela da arvore escolhida oferece o **caminho de volta** — `<a href="/">`, um `GET`, e **nao** uma `action` — e diz **qual arvore esta aberta** pelo nome visivel, sem a chave (`D-09`). Antes desta regra a tela tinha **zero** `<a href>`: a unica saida era recarregar ou digitar o endereco. O link, e nao uma `action`, porque nao passa pelo despacho da rota e por isso nao corre o risco de cair no `render_template` do fim e descartar o estado — defeito ja medido no `selecionar_arvore` | **pergunta do operador em 2026-10-10** |
| `RF-09` | A lista marca o item inalcancavel, com o motivo, sem esconde-lo | idem |

## 4. Divergencias declaradas

1. **A aplicacao atual perde o estado inicial do legado.** O pipeline de migracao
   (`_reversa_sdd/migration/`, 35 arquivos, cenarios `@paridade-visual` ancorados em `SCR-001`) foi
   desenhado sobre a tela antiga. Nada fica errado, mas a divergencia precisa ser lida (`D-06`).
2. **Conflito com a feature 009, RESOLVIDO em 2026-10-09.** `test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte`
   prendia o `GET /` por SHA fixo. A constante foi **atualizada** (`4b7f0b0c…` → `e18d1749…`, de 23.906
   para 25.825 bytes), com o comentario registrando quem mudou a tela e por que. Nao foi afrouxamento: o
   comentario anterior da propria constante declarava o criterio — "qualquer mudanca aqui e mudanca de
   tela, e nao desta feature". A suite final e **381 passed, 9 skipped, zero falhas**.
3. **O rotulo deixa de anunciar o tipo do arquivo, e isso foi MEDIDO e aceito em 2026-10-09.** A `RN-13`
   foi pedida pelo operador, e eu recomendei preservar a extensao; a decisao dele foi tirar as duas
   coisas. A consequencia medida na pasta real (19 arquivos): `Familias_Sergipanas.csv.ged`, que esta na
   aba de arvore porque o nome termina em `.ged`, passa a exibir `Familias Sergipanas csv` — o `csv`
   sobrevive como palavra, e **esse** e o unico sinal que resta do tipo real. Na aba de DNA, os itens
   `Familias_Sergipanas.csv` (usavel) e `Famílias_Sergipanas.csv` (inalcancavel, `BUG-20261009-6RKP`)
   ficam com rotulos que diferem **so pelo acento do `i`**, e a marca de indisponivel passa a ser o
   diferenciador principal. Nenhuma das duas coisas e defeito novo — antes da `RN-13` os nomes tambem
   diferiam so pelo acento —, mas o rotulo agora e uma frase, e nao um nome de arquivo, entao a
   diferenca fica mais discreta. Reverter e uma linha: a formatacao esta isolada em `rotulo_limpo`.
   A suite final e **395 passed, 9 skipped, zero falhas**.
4. **A aplicacao passou a MOVER arquivo do operador, e isso e novo em 2026-10-10.** Ate a `RN-14`, nenhum
   caminho do codigo movia nem apagava nada depois da gravacao: `grep` por `os.remove`, `unlink`,
   `rmtree` e `shutil.move` em `src/` nao encontrava **nenhuma** ocorrencia. Agora `aposentar` usa
   `os.replace` para levar o arquivo a `<pasta>/_aposentados/`. E o ponto de maior risco desta feature, e
   por isso: a `RN-07` ("a aplicacao nunca apaga arquivo enviado") **continua valendo** e ganhou teste
   proprio (`test_aposentar_nao_apaga_e_o_conteudo_esta_intacto`); a subpasta fica **dentro** da pasta de
   upload justamente para a operacao ser reversivel por um `mv` de volta; e a gravacao **nao sobrescreve**
   um aposentado de mesmo nome — acrescenta sufixo. A operacao **tem confirmacao na tela**, pedida pelo
   operador na mesma sessao: a caixa cita o arquivo daquela linha e avisa que ele continua guardado no
   disco. **Limite honesto:** a suite prende o atributo `onsubmit` no markup entregue, e isso e menos do
   que provar que a caixa aparece — `confirm` e do navegador, e nao ha motor de JavaScript na suite. A
   suite final e **430 passed, 9 skipped, zero falhas**.

## 5. O que este adendo NAO faz

- **Nao fecha o `BUG-20261009-6RKP`.** O gravador preserva acento e espaco no nome visivel, o resolvedor
  os recusa, e 7 dos 19 arquivos ficam inalcancaveis por referencia. A `011` **marca** o item
  indisponivel e **nao** conserta o contrato do nome — consertar mexe na defesa contra escape de
  caminho, e isso e trabalho do bug, com auditoria propria.
- **Nao recaptura golden nenhum.**
- **Nao fecha a divida 8** (`architecture.md` §7): a aplicacao continua sem estado entre requisicoes.
