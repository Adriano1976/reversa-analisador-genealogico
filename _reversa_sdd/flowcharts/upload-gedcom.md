# Fluxograma — módulo `upload-gedcom`

> Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração, nível **completo**).
> Fontes: `src/application/upload_gedcom.py`, `src/application/reenvio.py`, `src/utils/validate.py`, `src/parsers/gedcom_parser.py`, `src/utils/text_cleaning.py`, `src/ports/adaptadores.py` (as duas portas de arquivo), `src/core/erros.py`, `src/app.py` (ramo `upload_gedcom`).
> Substitui o fluxograma de 2026-10-05, que descrevia o estado global e a ausência de reenvio.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. Fluxo do envio (`POST /` com `action=upload_gedcom`)

```mermaid
flowchart TD
    A[POST / com action=upload_gedcom] --> B{campo gedcom em request.files?}
    B -- nao --> B1[Nenhum arquivo GEDCOM enviado] --> Z[index.html success=False]
    B -- sim --> C{filename vazio?}
    C -- sim --> C1[Nenhum arquivo selecionado] --> Z
    C -- nao --> D[gedcom_file.read - conteudo inteiro em memoria]
    D --> E[caso_de_uso_de_upload conteudo, nome, DONO_DO_PROCESSO, ARMAZENAMENTO, CARREGADOR]
    E --> F[guardar_com_substituicao tipo=gedcom]
    F --> G[FOTO DE ANTES: listar a pasta e guardar os NOMES]
    G --> H[armazenamento.guardar conteudo, nome, tipo, dono]
    H --> I{tipo == gedcom?}
    I -- sim --> J[validar_conteudo_gedcom]
    I -- nao --> K[pula a validacao de conteudo]
    J --> L{motivo?}
    L -- vazio / binario / nao comeca com 0 HEAD --> L1[recusa: devolve motivo, NAO grava] --> Z2[GedcomNaoSuportado - traducao - index.html success=False]
    L -- None --> M[chave = sha256 do conteudo, 16 hex]
    K --> M
    M --> N[nome armazenado = chave + __ + nome visivel seguro]
    N --> O{arquivo ja existe no disco?}
    O -- sim --> P[NAO reescreve]
    O -- nao --> Q[grava os bytes]
    P --> R[RN-17: versoes anteriores de MESMO nome visivel]
    Q --> R
    R --> S[aposentar cada versao anterior - move para _aposentados/]
    S --> T{quantas foram aposentadas?}
    T -- maior que 0 --> U[desfecho = substituido]
    T -- zero --> V{a referencia ja existia na foto de antes?}
    V -- sim --> W[desfecho = identico]
    V -- nao --> X[desfecho = novo]
    U --> Y{motivo veio preenchido?}
    W --> Y
    X --> Y
    Y -- sim --> Y1[raise GedcomNaoSuportado motivo]
    Y -- nao --> AA[referencia = basename do caminho]
    AA --> AB[carregador.carregar referencia, dono]
    AB --> AC{arvore is None?}
    AC -- sim --> AC1[RuntimeError: a arvore recem-gravada nao pode ser relida]
    AC -- nao --> AD[monta a MENSAGEM pelo desfecho]
    AD --> AE[nomes_de_exibicao - lista ordenada de get_name]
    AE --> AF[ResultadoDeUpload: referencia, nome_exibido, nomes, mensagem]
    AF --> AG[index.html com gedcom_filename, all_names, message, success=True]
```

## 2. As tres mensagens do reenvio (`RN-17`, pedido do operador em 2026-10-10)

```mermaid
flowchart LR
    A[Reenvio de um arquivo] --> B{mesmo nome visivel e mesmo conteudo?}
    B -- sim --> B1[identico: nada foi gravado]
    B1 --> B2["Arquivo 'X' ja estava armazenado com o mesmo conteudo: nada mudou."]
    A --> C{mesmo nome visivel e conteudo DIFERENTE?}
    C -- sim --> C1[substituido: a versao anterior vai para _aposentados/]
    C1 --> C2["Arquivo 'X' atualizado: a versao anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."]
    A --> D{nome visivel inedito?}
    D -- sim --> D1[novo: nada e aposentado]
    D1 --> D2["Arquivo 'NOME ORIGINAL' carregado! - literal CONGELADO, com o nome do formulario"]
```

## 3. A ordem que a `RN-17` exige: listar ANTES de guardar

```mermaid
sequenceDiagram
    participant UC as application/reenvio.py
    participant P as ArmazenamentoEmDisco
    participant FS as sistema de arquivos
    UC->>P: listar(dono)
    P->>FS: listdir + stat (NAO abre conteudo)
    FS-->>P: nomes, bytes, mtime
    P-->>UC: foto de ANTES
    UC->>P: guardar(conteudo, nome, tipo, dono)
    P->>P: valida conteudo (so gedcom) e deriva a chave
    P->>FS: escreve somente se o caminho NAO existir
    P-->>UC: (caminho, motivo)
    Note over UC: so a foto de ANTES separa<br/>"ja existia" de "acabou de nascer",<br/>porque guardar nao sobrescreve
    UC->>P: aposentar(versao anterior) por nome visivel igual
    P->>FS: os.replace para _aposentados/
```

## 4. Leitura da referencia em requisicao posterior

```mermaid
flowchart TD
    A[POST / com gedcom_filename no formulario] --> B{referencia presente?}
    B -- nao --> B1["Erro: Arquivo GEDCOM nao encontrado."]
    B -- sim --> C[_CARREGADOR.carregar referencia, DONO_DO_PROCESSO]
    C --> D[ArmazenamentoEmDisco.resolver]
    D --> E{chave_recebida_e_valida?}
    E -- nao --> E1[None - nenhum acesso ao disco acontece antes disso]
    E -- sim --> F{os.path.exists?}
    F -- nao --> F1[None]
    F -- sim --> G[carregar_arvore: GedcomReader]
    G --> H{parse levantou?}
    H -- sim --> H1[log do traceback + mensagem 'nao pode ser lido como GEDCOM'] --> Z[index.html success=False]
    H -- nao --> I["(people, families, graph, child_to_family)"]
    E1 --> J["Erro: Arquivo 'ROTULO' nao existe mais."]
    F1 --> J
    I --> K[segue para o ramo da action pedida]
```

## 5. Algoritmos e decisoes nao triviais

| # | Decisao | Onde | Por que |
| --- | --- | --- | --- |
| A1 | Chave de armazenamento derivada do **conteudo** (`sha256` truncado em 16 hex) | `utils/validate.py:chave_de_armazenamento` | O formulario devolve `gedcom_filename` no POST seguinte; um UUID aleatorio quebraria a continuidade entre requisicoes, e a mesma arvore reenviada reencontra o mesmo arquivo |
| A2 | Validacao por **conteudo** (`0 HEAD`), nunca por extensao | `utils/validate.py:validar_conteudo_gedcom` | `RISK-007`: exigir extensao recusaria GEDCOM de exportador legitimo e quebraria a paridade de parsing |
| A3 | Defesa contra escape de pasta por **forma de NOME**, e nao por alfabeto fechado | `utils/validate.py:chave_recebida_e_valida` e `:referencia_de_arquivo_da_pasta` | O alfabeto `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` recusava o acento e o espaco que o gravador **preserva de proposito** (`RF-06`); 3 arquivos com acento e 1 com espaco ficavam inalcancaveis (`BUG-20261009-6RKP`, `RN-20`) |
| A4 | Duas perguntas diferentes, duas funcoes | `_PREFIXO_CHAVE` (tem chave?) vs `chave_recebida_e_valida` (posso resolver?) | Sem a distincao, o arquivo acentuado cairia no mesmo balde do arquivo sem chave, e a tela diria ao operador a coisa errada sobre o proprio arquivo |
| A5 | A extensao e **preservada**, nunca fixada em `.ged` | `utils/validate.py:nome_visivel_seguro` | O mesmo gravador serve ao CSV: fixar `.ged` renomeava o CSV para `<...>.csv.ged` — regressao do proprio `QMLY`, corrigida em 2026-10-02 |
| A6 | `aposentar` move em vez de apagar, com sufixo numerico em vez de sobrescrever | `ports/adaptadores.py:aposentar` | `RN-07` proibe apagar. Para nomes **sem** chave o nome nao carrega conteudo, e sobrescrever apagaria outro arquivo; depois de 99 tentativas a funcao **desiste** (`False`) em vez de sobrescrever |
| A7 | A pasta de aposentados e uma **subpasta** da pasta de upload | `ports/adaptadores.py:PASTA_DE_APOSENTADOS` | `listar` ja ignora subdiretorio: o arquivo sai da lista **sem** nenhum filtro novo, e sem uma lista de excecoes que alguem teria de manter |
| A8 | Pasta ausente devolve lista vazia, e **nao** e criada | `ports/adaptadores.py:listar` | Criar diretorio dentro de uma leitura seria efeito colateral escondido numa operacao que promete nao escrever (`D-07`) |
| A9 | Leitura por atributos (`os.stat`), sem `open` | `ports/adaptadores.py:listar` | A tela de entrada e montada em toda renderizacao; abrir conteudo custaria reler os 29 MB da pasta (`RNF` de desempenho) |
| A10 | Os 18 pares de mojibake e a identidade `Ã -> Ã` | `utils/text_cleaning.py:strip_bad_utf` | Mapa herdado, medido por AST na rodada anterior; a faixa `Á-ú` da expressao de limpeza e **redundante**, porque `\w` ja e Unicode-aware |

## 6. Observações e lacunas

* 🟡 **A mensagem de "novo" usa `nome_original`, e nao o nome visivel seguro.** Os dois divergem quando o operador envia um nome com separador de caminho ou so com pontos. E o literal congelado ("Arquivo '...' carregado!"), preservado de proposito.
* 🟢 **O ramo `identico` só existe porque a foto de antes é tirada.** `guardar` nao sobrescreve, entao depois dele "ja existia" e "acabou de nascer" sao indistinguiveis na pasta.
* 🟢 **`aposentar` pode mover MAIS de uma versao anterior** na mesma operacao (`versoes_anteriores`): o operador ja tinha duas linhas do mesmo rotulo antes de a `RN-17` existir, e o reenvio limpa o acumulo.
* 🔴 **Nao ha validacao de conteudo para o CSV** (`tipo == "csv"` pula `validar_conteudo_gedcom`): a assimetria e divida preservada de proposito (`RF-10`), e o numero da divida segue aberto.
* 🔴 **`dono` nao participa de decisao nenhuma** nas tres portas: dois envios do mesmo conteudo chegam ao MESMO arquivo (`RN-02`), e nenhuma entrega pode ser citada como tendo implementado isolamento (dividas #3 e #4).
* 🔴 **O caso `RuntimeError("a árvore recém-gravada não pôde ser relida")` e inalcancavel em execucao**: `guardar` acabou de gravar o arquivo daquela referencia. Existe para o checador de tipos estreitar a uniao do retorno.

---

*Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração).*
