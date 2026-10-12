# Adendo: endurecimento da borda HTTP

> Identificador: `014-endurecimento-da-borda`
> Data: `2026-10-11`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)
> **Origem do registro:** escrito à mão, a pedido do operador, a partir de uma revisão adversarial de
> `src/app.py`. O canal canônico de adendo é o `/reversa-sync`; esta linha existe para que a próxima
> rodada saiba que o arquivo **não** saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-11.

**Nenhum literal de tela congelado foi alterado.** A seção "O que NÃO mudou" é o registro disso, e
existe porque a revisão que originou este adendo propôs mudar dois deles.

## Resumo da entrega

Cinco mudanças, todas em `src/app.py`. **Nenhuma linha de template foi tocada**, e por isso
`SHA_DA_TELA` (`f2b2233e…`) continua sendo o mesmo valor.

| # | O que mudou | Onde | Por quê |
|---|-------------|------|---------|
| 1 | `serve(..., max_request_body_size=TETO_DE_UPLOAD_EM_BYTES + MARGEM_DO_MULTIPART)` | bloco `__main__` | O `MAX_CONTENT_LENGTH` do Flask só age depois que o Flask recebe o `environ`, e o waitress acumula o corpo **antes** disso. O padrão do waitress é **1 GB** (`1073741824`), então o teto de 16 MB não impedia nada na camada de baixo — a classe do `BUG-20260929-QMLY` sobrevivia uma camada abaixo da correção que a declarou fechada |
| 2 | `rotulo_de_referencia(referencia_do_csv)` na mensagem de CSV ausente | ramo `dna_analysis` | A única mensagem do arquivo que ainda mostrava a **chave de conteúdo** de 16 hexadecimais. O docstring de `_arvore_do_formulario` declarava a regra — "o operador vê o NOME, nunca a chave, e o erro era o único lugar da tela que ainda a mostrava" — e esta linha irmã a contrariava |
| 3 | `except HTTPException: raise` antes do `except Exception`, nos três ramos | `upload_gedcom`, `dna_analysis`, `path_search` | Um erro de **cliente** era engolido pelo `except Exception` e virava **`200` com o texto interno do Werkzeug na tela**. Medido: `action=dna_analysis` sem `root_name` respondia `200` com "Ocorreu um erro: 400 Bad Request: The browser (or proxy) sent a request that this server could not understand." |
| 4 | `app.logger.exception(...)` nos três `except Exception` | idem | Fecha a lacuna que a extração já registrava como **🔴 "Nada é registrado em log"** em `upload-gedcom/contracts.md`, `analise-dna/contracts.md` e `busca-caminho/contracts.md`. Era o **único** `except` com rastro em 693 linhas, e estava justamente no caminho que já era protegido |
| 5 | `.strip()` no `root_name`, com guarda do vazio | ramo `dna_analysis` | A busca de caminho já fazia `.strip()` nos dois nomes; a análise de DNA não. Medido: `root_name='Carlos Silva Souza '` **não analisava** — "Seu nome 'Carlos Silva Souza ' não foi encontrado" —, e `' Carlos Silva Souza'` também não |

### A guarda do vazio no item 5, e por que ela não é zelo excessivo

O núcleo casa a raiz por `root_name.lower() in nome` (`core/dna_analysis.py:125-126`). Em Python,
`"" in "qualquer coisa"` é **verdadeiro**: um nome que virasse vazio depois do `strip()` casaria com
**todas** as pessoas da árvore, e `root_person_ids[0]` escolheria a **primeira** — a análise sairia,
com sucesso, sobre a pessoa errada. Por isso o valor **bruto** volta quando o `strip()` esvazia, e o
núcleo levanta `PessoaNaoEncontrada` como sempre. Medido: `root_name='   '` continua respondendo
"Seu nome '   ' não foi encontrado no GEDCOM."

## O que NÃO mudou, e por que

A revisão propôs trocar as duas mensagens de falha inesperada por uma frase genérica, para não vazar
detalhe interno. **As duas são literais de contrato congelados** e ficaram intactas:

| Literal | Onde está congelado |
|---------|---------------------|
| `"Ocorreu um erro: {e}"` | `analise-dna/contracts.md` §literais (`BR-D-93`), `busca-caminho/contracts.md` (`BR-C-65`), `domain.md` §5.1, `upload-gedcom/contracts.md`. `_reversa_forward/006/actions.md` (`T019`) manda explicitamente manter o `except Exception` de último recurso com este literal **intacto** |
| `"Erro ao processar GEDCOM: {e}"` | `upload-gedcom/contracts.md` §literais, `upload-gedcom/design.md` §5 |

O vazamento de `{e}` é, portanto, **comportamento declarado** — não um defeito que passou. Quem
quiser mudá-lo precisa de uma decisão que revogue os literais nos três contratos, e não de uma edição
pontual. O item 4 (log) resolve a metade que a extração já apontava como lacuna sem tocar no texto.

Também **não** foi alterado o `status` das telas de erro de domínio: `traduzir()` devolve
`RespostaDeErro(mensagem, status)` com `404`/`422`, e o adaptador usa só a `.mensagem`. Isso é a
`RN-05`, declarada em `application/traducao.py` e presa por
`tests/test_traducao_de_erros.py::test_status_da_traducao_nao_tem_consumidor_no_adaptador_de_entrada`,
que inspeciona o fonte de `src/app.py` para garantir que ninguém passe a ler a coluna. **O item 8 da
revisão ("erros devolvem 200") é regra registrada, não defeito.**

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/upload-gedcom/contracts.md` | literais; "Nada é registrado em log 🔴" | regra-alterada | A lacuna de log deixa de valer: os três `except Exception` registram rastro. Os literais **continuam** |
| `_reversa_sdd/analise-dna/contracts.md` | idem | regra-alterada | Idem |
| `_reversa_sdd/busca-caminho/contracts.md` | idem | regra-alterada | Idem |
| `_reversa_sdd/analise-dna/contracts.md` | entrada do ramo `dna_analysis` | delta-de-contrato-externo | `root_name` passa a ser lido com `.strip()`. Um nome com espaço nas bordas passa a ser aceito — o texto das mensagens não muda |
| `_reversa_sdd/domain.md` | §5.1 mensagens da camada de rota | sem-impacto | Nenhum dos 10 literais mudou |
| `_reversa_sdd/inventory.md` | pontos de entrada | delta-de-contrato-externo | O servidor passa a limitar o corpo que **recebe**, e não só o que o Flask aceita processar. A tabela de configuração de execução ganha `max_request_body_size` como limite efetivo |
| `tests/` | — | **sem-impacto** | `586 passed, 9 skipped`, os mesmos de antes. Nenhum teste mudou |

## Dívidas declaradas, não fechadas

| # | O que é | Gravidade | Por que ficou aberta |
|---|---------|-----------|----------------------|
| E-01 | A mensagem de falha inesperada continua mostrando `{e}` ao operador | 🟡 | **É contrato congelado** nos três contratos. Fechar exige revogar os literais, com decisão registrada |
| E-02 | Sem verificação do cabeçalho `Host` (DNS rebinding) | 🟡 | Uma página maliciosa que resolva o próprio domínio para `127.0.0.1` fala com a aplicação em mesma origem e lê as árvores e os relatórios de DNA — **sem precisar de sessão**, então o argumento de "não há autenticação" não cobre este caso. O conserto é barato (lista de `Host` permitidos), e ficou separado por decisão do operador: uma lista estrita demais quebra o acesso por `localhost`, pelo `127.0.0.1:5080` do container e pelo IP da máquina se `ANALISADOR_HOST=0.0.0.0` for usado |
| E-03 | Acima de ~17,8 MB, o corte é do waitress e a mensagem amigável não aparece | 🟢 | Consequência aceita do item 1: a margem de 1 MB preserva a mensagem da aplicação na faixa próxima do teto, e um arquivo muito maior recebe o erro do servidor. O custo evitado (receber centenas de MB para recusar no fim) vale mais do que a redação |
| E-04 | A requisição sem `root_name` passa a mostrar a página `400` do Flask, e não o cartão da aplicação | 🟢 | O status está correto agora, mas a tela é a padrão do Flask. Renderizar o cartão com uma frase amigável exigiria um literal novo — decisão que não estava no escopo destes cinco itens |

## Regras sob vigilância

| Item | Onde | Sinal de quebra |
|------|------|-----------------|
| O limite do waitress acompanha o teto do Flask | `src/app.py`, `MARGEM_DO_MULTIPART` | O `serve()` voltar a não passar `max_request_body_size`, ou o valor deixar de ser derivado de `TETO_DE_UPLOAD_EM_BYTES` |
| Os literais de falha inesperada | três `contracts.md` | O texto mudar sem revogação declarada nos contratos |
| `traduzir(...).status` continua sem consumidor | `tests/test_traducao_de_erros.py` | Um quarto `traduzir(...).mensagem`, ou uma leitura de `.status` no adaptador — o teste conta as ocorrências e falha |
| Os três `except Exception` registram rastro | `src/app.py` | Um `app.logger.exception` ser removido de um deles |

## Fontes

- `src/app.py` — as cinco mudanças, todas no adaptador de entrada
- `src/application/traducao.py` — `RespostaDeErro` e a `RN-05` da coluna sem consumidor
- `src/core/dna_analysis.py:125-126` — o casamento da raiz por `in`, origem da guarda do vazio
- `tests/test_traducao_de_erros.py` — o teste que inspeciona o fonte para prender a `RN-05`
- Revisão adversarial de 2026-10-11 do `app.py` (22 itens). Os itens aceitos são os cinco acima; o
  item 8 foi recusado por contrariar a `RN-05`, e os itens 1, 4, 5, 10, 13, 15, 17, 18 e 21 ficaram
  fora do escopo por serem decisão, contrato ou otimização sem problema medido
