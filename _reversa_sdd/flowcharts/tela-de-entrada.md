# Fluxograma — módulo `tela-de-entrada`

> Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração, nível **completo**).
> Fontes: `src/reporting/lista_de_arquivos.py`, `src/app.py` (`index` no ramo GET, `_listas_da_tela`, `_arvore_do_formulario`), `src/ports/adaptadores.py` (`listar` e `aposentar`), `src/utils/validate.py` (as duas perguntas sobre o nome).
> Módulo **novo** nesta rodada: nasceu nas features 011 e 012, e nao tem equivalente na extração de 2026-10-05.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. Rendering da tela de entrada (`GET /`)

```mermaid
flowchart TD
    A[GET /] --> B[render_template index.html]
    B --> C[processador de contexto _listas_da_tela]
    C --> D[_ARMAZENAMENTO.listar DONO_DO_PROCESSO]
    D --> E{pasta de upload existe?}
    E -- nao --> E1[devolve lista VAZIA - nao cria diretorio]
    E -- sim --> F[os.listdir + os.stat por entrada]
    F --> G[ignora subdiretorio - e o que faz _aposentados sumir da lista]
    G --> H[EntradaArmazenada: nome, bytes, modificado_em]
    H --> I[itens_da_aba entradas, .ged]
    H --> J[itens_da_aba entradas, .csv]
    I --> K[contexto: arvores_da_lista]
    J --> L[contexto: relatorios_da_lista]
    K --> M[template renderiza as duas abas SEMPRE]
    L --> M
    M --> N[colunas: rotulo, quantidade, tamanho, Enviado em, acoes]
```

## 2. De entradas da pasta a itens de lista (`itens_da_aba`)

```mermaid
flowchart TD
    A[entradas da pasta + extensao da aba] --> B[para cada entrada: decompor_nome_armazenado]
    B --> C{o nome VISIVEL termina com a extensao?}
    C -- nao --> C1[fora das duas abas: e o caso do .xlsx da pasta real]
    C -- sim --> D{tem chave de 16 hex?}
    D -- sim --> E[marca = com + chave - agrupa]
    D -- nao --> F[marca = sem + nome inteiro - NUNCA agrupa]
    E --> G[grupo]
    F --> G
    G --> H[_montar_item por grupo]
    H --> I[representante = o de maior mtime do grupo]
    I --> J[rotulo do grupo: prefere um visivel SEM chave]
    J --> K[quantidade, bytes somados, mtime do representante]
    K --> L[disponivel = pode_ser_usado - mesma funcao do resolvedor]
    L --> M[motivo_indisponivel = sem chave ou fora da forma]
    M --> N[ordena: mtime decrescente, empate pelo nome exibido]
    N --> O[itens da aba]
```

**Por que a marca "sem chave" carrega o nome inteiro:** dois arquivos **sem** chave nao podem cair no mesmo item — a chave nao os alcanca, e le-los para agrupar custaria os 29 MB que a listagem evita.

## 3. Aposentar um arquivo (`POST /` com `action=aposentar_arquivo`)

```mermaid
flowchart TD
    A[POST / action=aposentar_arquivo] --> B["referencia = request.form['arquivo_a_aposentar']"]
    B --> C[armazenamento.aposentar referencia, dono]
    C --> D{referencia_de_arquivo_da_pasta?}
    D -- nao --> D1[False - e um CAMINHO, nao um nome]
    D -- sim --> E{dirname do caminho resolvido == pasta de upload?}
    E -- nao --> E1[False - segunda camada, nao confia na primeira]
    E -- sim --> F{is file?}
    F -- nao --> F1[False]
    F -- sim --> G["destino = <pasta>/_aposentados/<referencia>"]
    G --> H{ja existe aposentado com esse nome?}
    H -- sim --> I[acrescenta .1 .2 ... ate achar livre]
    I --> J{achou em ate 99 tentativas?}
    J -- nao --> J1[False - desiste em vez de sobrescrever]
    J -- sim --> K[os.replace origem, destino]
    H -- nao --> K
    K --> L{moveu?}
    L -- sim --> L1["'ROTULO' saiu da lista. O arquivo nao foi apagado: ele continua guardado, inteiro, na pasta de aposentados."]
    L -- nao --> L2["Nao foi possivel aposentar o arquivo: ele nao esta mais na pasta."]
```

> 🟢 **A ordem dos ramos é a regra, e não estilo.** `aposentar_arquivo` vem **antes** de `_arvore_do_formulario()`, porque essa funcao resolve e **parseia** a arvore escolhida — e a arvore escolhida pode ser exatamente a que se esta aposentando. Depois do move, o parse falharia e o operador veria "arquivo nao existe mais" no lugar da confirmacao: a acao teria funcionado e a tela diria que nao.

## 4. Escolher uma arvore da lista (`POST /` com `action=selecionar_arvore`)

```mermaid
flowchart TD
    A[POST / action=selecionar_arvore] --> B[_arvore_do_formulario]
    B --> C{referencia presente?}
    C -- nao --> C1["Erro: Arquivo GEDCOM nao encontrado."]
    C -- sim --> D[_CARREGADOR.carregar referencia, dono]
    D --> E{arvore is None?}
    E -- sim --> E1["Erro: Arquivo 'ROTULO' nao existe mais."]
    E -- nao --> F[nomes_de_exibicao arvore]
    F --> G[render index.html COM gedcom_filename e all_names]
    G --> H[mesmo estado que o envio produz: a tela da arvore escolhida]
```

> 🟢 **Por que o ramo existe:** sem ele, este `action` cairia no `return` do fim de `index()`, que renderiza `index.html` **sem** `gedcom_filename` — a arvore resolvida seria descartada e o operador clicaria sem nada acontecer. Era o defeito medido em 2026-10-09 (`RF-02` da feature 012).

## 5. Algoritmos e decisoes nao triviais

| # | Decisao | Onde | Por que |
| --- | --- | --- | --- |
| B1 | As duas listas entram por **processador de contexto** | `src/app.py:_listas_da_tela` | A rota tem **23** `render_template` (medidos em 2026-10-10; **12** passam `gedcom_filename`); repetir o argumento em cada um seria 23 lugares para esquecer um |
| B2 | **Nao ha `os.listdir` na rota** | `src/app.py` | Quem le a pasta e a **porta**; um `listdir` na borda traria de volta o acesso a disco que a feature 006 tirou de la |
| B3 | Agrupamento pela chave de conteudo, item proprio quando nao ha chave | `lista_de_arquivos.py:itens_da_aba` | `RN-01` e `RN-10`: agrupar o sem-chave exigiria ler o conteudo |
| B4 | A aba e decidida pela extensao do **nome visivel cru** | `itens_da_aba` | `RN-03`/`D-10`: `planilha.csv.ged` entra na aba de arvore mesmo tendo conteudo de CSV; quem recusa e o USO (`D-08`) |
| B5 | O item indisponivel **aparece marcado**, com motivo | `_montar_item` | `RN-11`/`D-11`: esconder o inalcancavel tiraria do operador o arquivo que ele mais quer aposentar |
| B6 | Dois motivos distintos de indisponibilidade | `validate.py:motivo_de_indisponibilidade` | "sem chave" (arquivo anterior a chave por conteudo) e "fora da forma" (acento/espaco recusados) — dizer "sem chave" para o acentuado seria mentir sobre o motivo |
| B7 | Rotulo sem chave vazada | `lista_de_arquivos.py:_rotulo_do_grupo` | Caso medido: o grupo passou a ter dois rotulos porque o operador reenviou um arquivo ja chaveado; exibir o primeiro em ordem alfabetica mostraria a chave crua |
| B8 | Rotulo tira **so a ultima** extensao | `lista_de_arquivos.py:rotulo_limpo` | `planilha.csv.ged` vira `planilha csv`: o `.csv` do meio e informacao que o `D-08` decidiu **nao** esconder |
| B9 | Ordem por data decrescente, empate pelo nome | `itens_da_aba` | O nome exibido **nao e unico**: ha tres `Arvore_Unificada_Oficial_V1_2.ged` na pasta real; a data e o que distingue |
| B10 | Data vem de `os.stat`, e a coluna se chama "Enviado em" | `formatar_data_br` | Para arquivo guardado pela aplicacao e a data do envio; quem copia a mao muda a data, e o `title` da coluna declara isso |
| B11 | Data que o sistema nao converte devolve **celula vazia** | `formatar_data_br` | `OverflowError`/`OSError` viraria `500` **na tela que lista tudo** por causa de uma celula |
| B12 | A tela pergunta a **mesma** funcao que o resolvedor | `validate.py:pode_ser_usado` | Dois testes equivalentes divergem com o tempo, e a tela passaria a dizer "disponivel" para um arquivo que o resolvedor recusa (`D-11`) |

## 6. Observações e lacunas

* 🟢 **O instrumento de paridade nao enxerga as listas.** `_reversa_sdd/parity/harness.py` substitui `render_template` por uma captura de contexto, entao o processador de contexto nem chega a rodar. Acrescentar chave ao contexto e invisivel para ele, **por construcao** — o que e uma lacuna de cobertura do harness, nao um defeito.
* 🟡 **A quantidade do grupo e o numero de ARQUIVOS, e nao de versoes uteis.** Depois de uma substituicao o grupo fica com um arquivo; mas se o operador reenviar duas vezes o mesmo nome com conteudos diferentes **sem** passar pela aplicacao (copiando a mao), o grupo volta a ter dois.
* 🔴 **A listagem nao filtra nada**, por decisao: nem por nome, nem por extensao, nem por forma da chave. Filtrar no adaptador esconderia do operador um arquivo que existe — mas tambem significa que a pasta e a superficie de confianca da tela.

---

*Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração).*
