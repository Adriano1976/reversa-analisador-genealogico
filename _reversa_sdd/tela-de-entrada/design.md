# Unit `tela-de-entrada` — Design Técnico

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Unit **nova**.
> Fontes: `reporting/lista_de_arquivos.py`, `app.py` (`_listas_da_tela`, `index`, `_arvore_do_formulario`), `ports/adaptadores.py` (`listar`, `aposentar`), `utils/validate.py`, `templates/index.html`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Interface

### Endpoint HTTP

| Método | Caminho | Ação | Entrada | Saída | Status |
|--------|---------|------|---------|-------|--------|
| GET | `/` | — | — | `index.html` com `arvores_da_lista` e `relatorios_da_lista`; sem `gedcom_filename` | 200 |
| POST | `/` | `aposentar_arquivo` | `arquivo_a_aposentar` = **nome armazenado** | `index.html` com `message` e `success` | 200 |
| POST | `/` | `selecionar_arvore` | `gedcom_filename` = **nome armazenado** | `index.html` com `gedcom_filename` + `all_names` | 200 |

> O `POST /` é **único** e multiplexado por `action`: as 5 ações (`upload_gedcom`, `aposentar_arquivo`, `selecionar_arvore`, `dna_analysis`, `path_search`) compartilham a mesma rota. Esta unit cobre `GET`, `aposentar_arquivo` e `selecionar_arvore`; `upload_gedcom` é da unit homônima, e as duas últimas de `analise-dna` e `busca-caminho`. 🟢

### Símbolos

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `_listas_da_tela` | `()` | `dict` | Processador de contexto: roda em **toda** renderização de `index.html`; injeta as duas listas 🟢 |
| `itens_da_aba` | `(entradas: Iterable[Entrada], extensao: str)` | `list[ItemDaLista]` | **Pura**: não abre arquivo, não toca disco 🟢 |
| `decompor_nome_armazenado` | `(nome)` | `(chave \| None, visivel)` | `(None, "")` para não-`str` ou vazio; não decide alcançabilidade 🟢 |
| `rotulo_limpo` | `(nome_visivel: str)` | `str` | Tira a última extensão e troca símbolos por espaço 🟢 |
| `rotulo_de_referencia` | `(nome_armazenado: str)` | `str` | Rótulo a partir do **nome armazenado**, sem montar a lista 🟢 |
| `formatar_data_br` | `(modificado_em: float)` | `str` | `dd/mm/aaaa`; `""` se não converter 🟢 |
| `motivo_de_indisponibilidade` | `(nome)` | `str \| None` | Dois literais distintos, ou `None` 🟢 |
| `pode_ser_usado` | `(nome)` | `bool` | Delega para `chave_recebida_e_valida` 🟢 |
| `_arvore_do_formulario` | `()` | `(referencia, arvore, erro)` | Lê `request.form['gedcom_filename']`; **compartilhada** com `analise-dna` e `busca-caminho` 🟢 |
| `ItemDaLista` | `@dataclass(frozen=True)` | — | 8 campos; `nome_exibido` e `nome_armazenado` **nunca** são a mesma string 🟢 |
| `ArmazenamentoEmDisco.listar` | `(dono: str)` | `list[EntradaArmazenada]` | `dono` recebido e **ignorado** 🟢 |
| `ArmazenamentoEmDisco.aposentar` | `(referencia: str \| None, dono: str)` | `bool` | `dono` recebido e **ignorado** 🟢 |

### Contrato de contexto do template

| Chave | Tipo | Quem escreve | Consumidor |
|-------|------|--------------|------------|
| `arvores_da_lista` | `list[ItemDaLista]` | `_listas_da_tela`, com `extensao=".ged"` | tabela da aba "Buscar Conexão no GEDCOM" 🟢 |
| `relatorios_da_lista` | `list[ItemDaLista]` | `_listas_da_tela`, com `extensao=".csv"` | tabela da aba "Analisador de DNA" e o `<select>` de CSV da análise 🟢 |
| `gedcom_filename` | `str \| None` | a rota, em 12 das 23 renderizações | campo oculto dos formulários; filtro `rotulo_do_arquivo` na faixa "Árvore aberta" 🟢 |
| `all_names` | `list[str]` | a rota, via `nomes_de_exibicao(arvore)` | `<datalist>` dos formulários de análise 🟢 |
| `message`, `success` | `str`, `bool` | a rota | faixa de alerta no topo 🟢 |

> 🟢 Medição de 2026-10-10: `app.py` tem **23** `render_template(...)` e **12** deles passam `gedcom_filename`. O comentário em `app.py:105-106` afirma "oito renderizações com `gedcom_filename`" — número **desatualizado**, e a conclusão a que ele serve (usar filtro em vez de parâmetro repetido) continua correta e fica **mais** forte com 12.

## Fluxo Principal

### 1. `GET /` — a tela se monta sem ação do operador

1. Flask resolve a rota `index` (`app.py:357-358`) e, como o método é `GET`, nenhum ramo de `action` é avaliado. 🟢
2. Antes de renderizar, **todo** processador de contexto registrado roda — e o único da aplicação é `_listas_da_tela` (`app.py:341-353`). 🟢
3. `_listas_da_tela` chama `_ARMAZENAMENTO.listar(DONO_DO_PROCESSO)` **uma vez** e pergunta a `itens_da_aba` **duas vezes**, uma por extensão. 🟢
4. `listar` (`adaptadores.py:143-162`): se a pasta não é diretório, devolve `[]` **sem criar nada**; senão, `os.listdir`, descarta o que não é arquivo (`isfile`), faz `os.stat` de cada um, descarta o que sumiu entre o `listdir` e o `stat`, e devolve `EntradaArmazenada(nome, bytes, modificado_em)`. **Nenhum `open`.** 🟢
5. `itens_da_aba` (`lista_de_arquivos.py:146-178`): decompõe cada nome, filtra por `visivel.endswith(extensao)`, agrupa por `("com", chave)` ou `("sem", entrada.nome)` inteiro, monta um item por grupo e ordena por `(-mtime, nome_exibido)`. 🟢
6. `_montar_item` (`:181-194`): representante = `max(grupo, key=mtime)`; o item leva rótulo do grupo, quantidade, soma dos bytes, disponibilidade e motivo **do representante**. 🟢
7. `index` cai no `return render_template("index.html")` final (`app.py:530`) — **sem** `gedcom_filename`. O template entra no ramo `{% if not gedcom_filename %}` e desenha as duas abas com as listas e, dentro da aba de árvores, o formulário de envio. 🟢

### 2. `POST /` com `action=aposentar_arquivo`

1. `index` avalia a ação **antes** de qualquer chamada a `_arvore_do_formulario` (`app.py:381`). 🟢
2. Lê `request.form.get("arquivo_a_aposentar")` — o **nome armazenado**, que veio do campo oculto do item. 🟢
3. `_ARMAZENAMENTO.aposentar(referencia, DONO_DO_PROCESSO)` (`adaptadores.py:164-217`):
   - `referencia_de_arquivo_da_pasta` recusa caminho (barra, barra invertida, NUL, `..`, vazio, `.`) — **primeira camada**; 🟢
   - `os.path.dirname(os.path.abspath(origem))` tem de ser **exatamente** a pasta de upload — **segunda camada**, que não confia na primeira; 🟢
   - `isfile` confirma que ainda está lá; 🟢
   - `os.makedirs(<pasta>/_aposentados, exist_ok=True)`; 🟢
   - colisão de nome: sufixo `.1`…`.99`; esgotadas as 99, **desiste** (`False`) em vez de sobrescrever; 🟢
   - `os.replace(origem, destino)` — move, nunca apaga. 🟢
4. A rota responde com o literal de sucesso, que **diz que nada foi apagado**, ou com o de fracasso (`app.py:394-404`). 🟢
5. A lista se reconstrói sozinha na renderização seguinte: o arquivo agora está em subpasta, e `listar` ignora subdiretório. **Nenhum filtro novo foi escrito para isso.** 🟢

### 3. `POST /` com `action=selecionar_arvore`

1. Chega ao bloco comum: `_arvore_do_formulario()` (`app.py:406`). 🟢
2. `_arvore_do_formulario` (`:173-235`) lê `gedcom_filename`; ausente → `(None, None, "Erro: Arquivo GEDCOM não encontrado.")`. 🟢
3. `_CARREGADOR.carregar(referencia, DONO_DO_PROCESSO)` → resolve pela porta (`chave_recebida_e_valida`) e **parseia**. Tudo dentro de `try`: falha de parse → `app.logger.exception` + mensagem de arquivo ilegível; `None` → `Erro: Arquivo 'ROTULO' não existe mais.` 🟢
4. `nomes_de_exibicao(arvore)` produz `all_names`. 🟢
5. O ramo `selecionar_arvore` (`:415-428`) renderiza `gedcom_filename` + `all_names` — o **mesmo** estado que o envio produz. 🟢

## Fluxos Alternativos

- **Pasta de upload ausente:** `listar` devolve `[]` e o `os.makedirs` que criaria o diretório **não** é chamado — criar diretório dentro de uma leitura seria efeito colateral escondido numa operação que promete não escrever. A tela mostra o estado vazio. 🟢
- **Arquivo que sumiu entre `listdir` e `stat`:** a entrada é pulada; a listagem é um retrato do instante. 🟢
- **Instante que `datetime.fromtimestamp` não converte** (`OverflowError`, `OSError`, `ValueError`): a célula de data sai vazia, e não `500`. 🟢
- **Aposentar a árvore que está aberta:** funciona, porque o ramo vem antes da resolução. Sem isso o operador veria "arquivo não existe mais" depois de a ação ter dado certo. 🟢
- **Aposentar arquivo já ausente:** `False` → `Não foi possível aposentar o arquivo: ele não está mais na pasta.` 🟢
- **100 aposentados com o mesmo nome:** desiste, para não sobrescrever um arquivo diferente. 🟢
- **Referência com forma válida e arquivo ausente:** `Erro: Arquivo 'ROTULO' não existe mais.` — com o **rótulo**, não a chave. 🟢
- **GEDCOM alcançado que o parser não lê:** mensagem em português, traceback no log. Medido: 10 dos 13 arquivos da pasta real chegavam a `500` antes desta guarda. 🟢
- **Aba de DNA sem relatórios:** estado vazio que **orienta para a aba ao lado**, e nenhum formulário de envio — não existe ação que guarde um CSV sozinho. 🟢

## Dependências

- `ports/` (`ArmazenamentoDeArquivos.listar` / `.aposentar`), razão de a unit **não** tocar disco: toda leitura de diretório e todo `move` atravessam a porta. `ADR-25`. 🟢
- `utils/validate.py`, autoridade única sobre a **forma do nome armazenado** e sobre a **elegibilidade da referência**; a tela pergunta a ela, e não a um teste próprio (`BR-T-10`). `ADR-32`. 🟢
- `reporting/lista_de_arquivos.py`, a função **pura** que transforma entradas em itens; pura para ser testável **sem disco**. 🟢
- `application.nomes_de_exibicao` (`application/__init__.py`), produtora de `all_names`. 🟢
- `ports/adaptadores.py:CarregadorDeArvoresGedcom`, o **único** lugar da fronteira que parseia — chamado por `_arvore_do_formulario`. 🟢
- `templates/index.html` e Bootstrap (via CDN), no markup das abas, tabelas e formulários. 🟡 *(o Bootstrap não é declarado em `requirements.txt`: é ativo de front-end, carregado no template)*
- Consumidores a jusante: `analise-dna` e `busca-caminho` dependem do `gedcom_filename` que **esta** unit entrega. 🟢

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| As listas entram por **processador de contexto**, e não por argumento repetido | `app.py:341-353`; 23 `render_template` no arquivo | 🟢 |
| A listagem é **pura** e mora em `reporting/`, não no adaptador nem no template | `lista_de_arquivos.py:5-27` — no adaptador misturaria apresentação com I/O; no template não haveria teste de unidade | 🟢 |
| A **aba** é decidida pela extensão do nome visível **cru**, não pelo conteúdo (`D-08`, `D-10`) | `lista_de_arquivos.py:166-168` | 🟢 |
| O arquivo **sem chave** carrega o **nome inteiro** na marca do grupo | `lista_de_arquivos.py:171` | 🟢 |
| O **rótulo do grupo** prefere um visível sem chave; se não houver, tira a chave do primeiro em ordem alfabética | `lista_de_arquivos.py:197-214` | 🟢 |
| O rótulo formata **no fim**, depois de tudo o que o nome decide | `lista_de_arquivos.py:97-107` | 🟢 |
| O item **indisponível** aparece marcado, e não escondido (`RN-11`, `D-11`) | `templates/index.html:145-155`, `:230-237` | 🟢 |
| A disponibilidade vem da **mesma** função do resolvedor (`D-11`) | `utils/validate.py:205-213` | 🟢 |
| O **`os.replace`** para `_aposentados/` dentro da própria pasta de upload: `listar` já ignora subdiretório, então nenhum filtro novo é necessário | `adaptadores.py:36-39`, `:202-216` | 🟢 |
| **Desistir** em vez de sobrescrever aposentado, depois de 99 tentativas: para nomes sem chave o nome não carrega conteúdo, e sobrescrever apagaria outro arquivo | `adaptadores.py:205-214` | 🟢 |
| A **ordem dos ramos** em `index` (aposentar antes de resolver a árvore) | `app.py:381-406` | 🟢 |
| O nome visível da árvore aberta é **filtro** de template (`rotulo_do_arquivo`), não parâmetro | `app.py:104-110` | 🟢 |
| A aba de DNA **não** ganha formulário de envio nem botão "Abrir": a rota não atende nenhum dos dois | `templates/index.html:242-248`, `:262-268` | 🟢 |
| A tabela não tem coluna de **identificador público**: a chave de conteúdo não pode ocupar esse lugar (`D-09`) | `templates/index.html:121-124` | 🟢 |

## Estado Interno

**A unit não mantém estado.** 🟢

- Não há variável de módulo com dados de requisição: `_ARMAZENAMENTO` e `_CARREGADOR` são **singletons de processo** montados no import (`app.py:141-142`), e guardam apenas a pasta resolvida uma vez — o ambiente não muda no meio do processo. 🟢
- `ItemDaLista` é `frozen=True`: cada renderização constrói itens novos a partir de uma leitura nova. Não há cache entre requisições, e portanto não há invalidação a manter. 🟢
- O "estado" que sobrevive entre requisições é o **campo oculto `gedcom_filename`** no HTML, devolvido pelo navegador — é assim que a aplicação mantém continuidade **sem sessão**. 🟢
- `DONO_DO_PROCESSO = "unico"` é constante de módulo, e atravessa as três chamadas de porta sem participar de decisão nenhuma. `ADR-26`. 🟢

## Observabilidade

| O quê | Onde | Observação |
|-------|------|------------|
| `app.logger.exception("GEDCOM alcancado pela referencia nao pode ser lido")` | `app.py:228` | Único log da unit; o traceback vai para o log e a frase para a tela 🟢 |
| Mensagem de falha de aposentadoria na tela | `app.py:401-404` | Não há log: uma tentativa de aposentar arquivo ausente não deixa rastro no servidor 🔴 |
| Nenhuma métrica, nenhum contador | — | Não há instrumentação de tempo de listagem nem de tamanho de pasta 🔴 |

## Riscos e Lacunas

- 🟢 **`L-30` — DECIDIDA em 2026-10-10: corrigir a docstring e MANTER o ramo.** `motivo_de_indisponibilidade` (`utils/validate.py:183-202`) justifica o segundo motivo dizendo que é "o caso do acento e do espaço, medido na pasta real". Mas a `_FORMATO_CHAVE` que recusava acento e espaço foi **removida em 2026-10-10** (`RN-20`, `ADR-32`), e `chave_recebida_e_valida` passou a exigir apenas que a parte visível seja um **nome**. Consequência verificada por leitura: um arquivo como `94e2402671702cac__Famílias_Sergipanas.csv` agora é **disponível**, e `FORA_DA_FORMA` só sobra para valores que não podem existir como entrada de diretório (barra, NUL) ou para o caso degenerado de parte visível vazia. **A decisão é manter o ramo como defesa em profundidade e corrigir o comentário** — o defeito é a docstring, não o código, e o ramo ainda cobre um caso legítimo. A correção do comentário é mudança de código em `src/utils/validate.py` e fica agendada para **depois do Passo 4**; a tarefa `T-06` fica **desbloqueada** com esta decisão.
- 🟢 **`L-31` — a disponibilidade do grupo é a do representante: MEDIDA em 2026-10-10 e sem consequência no dado real.** A pergunta era se um grupo "com chave" poderia ter membros com elegibilidade divergente. Medição sobre a pasta do operador: **13 grupos, nenhum com mais de um membro** — logo a divergência **não pode ocorrer** nos dados atuais, porque o agrupamento exige a mesma chave de conteúdo e nada no histórico da pasta produziu dois nomes visíveis para a mesma chave. **Decisão humana de 2026-10-10: manter** a decisão pelo representante. A lacuna passa a ser condicional: ela só reaparece se o operador reenviar o mesmo conteúdo com **outro nome**, e o gatilho é observável (o grupo passa a ter dois membros). **[Verificar] se vale um teste que falhe quando um grupo passar a ter dois membros** — é a forma barata de não depender de ninguém lembrar disto.
- 🟡 **`L-32` — a quantidade conta arquivos, não versões úteis.** Já registrado pelo Arqueólogo: se o operador copiar dois arquivos de mesmo nome e conteúdos diferentes **sem** passar pela aplicação, o grupo volta a ter dois itens legíveis para o operador.
- 🟢 **O instrumento de paridade não enxerga as listas.** `parity/harness.py` substitui `render_template` por uma captura de contexto, de modo que o processador de contexto **não roda**. Acrescentar chave ao contexto é invisível para ele **por construção** — é lacuna de cobertura do harness, não defeito da unit. Quem cobre esta unit é a suíte: **132** testes em **8** arquivos.
- 🔴 **A listagem não filtra nada, por decisão.** A pasta é a superfície de confiança da tela: um arquivo colocado ali por fora da aplicação (ou um `.xlsx`) aparece listado, e os **nomes** de tudo o que está na pasta ficam visíveis para qualquer cliente que alcance a porta — a aplicação não tem autenticação (`permissions.md`).
- 🟡 **`_arvore_do_formulario` é uma dependência compartilhada sem dono declarado.** Ela é a fonte única das guardas de entrada de três units (`tela-de-entrada`, `analise-dna`, `busca-caminho`), mas vive em `app.py` e não em um módulo próprio. Mudança nela altera o contrato das três. **[Verificar]** se a fronteira deveria nomear esse ponto.
- 🟡 **`listar` segue links simbólicos.** `os.path.isfile` segue o link, então um symlink na pasta aparece como arquivo, com o tamanho e a data do **alvo**. `aposentar` moveria o link (não o alvo). **Não medido**; exige escrita prévia na pasta para ser explorado, e a pasta já é a superfície de confiança.
- 🟢 **Nenhuma ação da lista escreve arquivo além do `os.replace`**, e `GET /` não tem efeito colateral: é o que permite a tela ser recarregada sem medo.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*
