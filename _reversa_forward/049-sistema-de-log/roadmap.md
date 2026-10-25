# Roadmap: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Requirements: `_reversa_forward/049-sistema-de-log/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A observabilidade entra como **três peças novas em `utils/` e uma na borda**, sem tocar o núcleo:
`utils/logs.py` (configuração, contexto de requisição, máscara de privacidade e medição),
`utils/auditoria.py` (a linha de auditoria tipada) e `web/hooks_de_registro.py` (a fiação Flask:
identificador, cabeçalho e linha de acesso). `app.py` passa a **chamar** a auditoria nos cinco
desfechos do `requirements` e troca o `print` de inicialização pelo logger; `ports/adaptadores.py`
ganha um `with medir("carregar_arvore")` no ponto único onde o parse acontece.

As três mensagens de tela mantêm o prefixo e perdem o `{e}` — mudança de contrato que **não é
cega**: o `modo()` do harness de paridade classifica o desfecho por prefixo
(`_reversa_sdd/parity/harness.py:185`), então a categoria continua a mesma e a paridade segue
comparável. A auditoria é emitida **só na borda**, porque IP e identificador de requisição são
HTTP e o núcleo não conhece HTTP.

Duas escolhas de operação sustentam a `RN-10`: o log geral rotaciona por tamanho (5 × 5 MB), e a
**auditoria não** — ela grava um arquivo por dia e nunca descarta dado por volume, porque descartar
por tamanho contradiria o prazo de 90 dias com expurgo manual.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca no versionamento | Logs são caminho proibido pelo próprio texto do princípio. A `RN-05` e a máscara implementam; a auditoria grava chave de conteúdo, nunca o rótulo do arquivo | respeita |
| II. Comportamento observável preservado | **CONFLITO DECLARADO**: as três mensagens de tela mudam de texto pela `RN-06`. É mudança de comportamento observável de propósito, e por isso percorreu requirements → clarify → plan em vez de se apresentar como refactor | **conflita (declarado)** |
| III. Nenhuma mudança sem teste | Quatro testes novos, um deles o de privacidade sobre a análise real com fixture sintética | respeita |
| IV. Arestas do grafo são tipadas | A feature não percorre o grafo | n/a |
| V. Toda suposição de genealogia cita a fonte | Os números citados (`20,9 s` de parse, `1,73 s` de dossiê, `1656` testes, `29` literais) vêm de `_reversa_sdd/` e do addendo 048 | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Uma função `configurar()` **idempotente** em `utils/logs.py`, chamada em `create_app()`, com guarda de módulo | A suíte cria a aplicação centenas de vezes; anexar handler por chamada duplicaria toda linha, e `basicConfig` só age na primeira chamada do processo — falha silenciosa | `basicConfig` (no-op a partir da 2ª vez); `dictConfig` (camada de configuração sem ganho medido) | 🟡 |
| D-02 | Dois loggers: o raiz (console + arquivo geral) e `auditoria` com `propagate=False` | É o único jeito de a linha de auditoria não virar eco no arquivo geral nem no console | um logger só, com filtro por nome de logger | 🟢 |
| D-03 | O identificador de requisição vive em `contextvars` | Sobrevive à requisição sem passar por parâmetro até o adaptador, e não vaza entre threads do pool | `flask.g` (não existe fora do contexto de requisição, e a medição roda em adaptador); `threading.local` (vaza quando a thread é reaproveitada) | 🟡 |
| D-04 | O cabeçalho `X-Request-ID` é **sempre gerado** e nunca aceito do cliente | Texto de cliente em arquivo de log é vetor de injeção de linha, e o `requirements` (`RF-03`) já fixou que não se reaproveita | aceitar o cabeçalho do cliente e validar o formato | 🟢 |
| D-05 | A máscara é um `Filter` no handler, que reescreve `msg`/`args` **e materializa `exc_text` mascarado**, zerando `exc_info` | É o único ponto que alcança o traceback sem editar cada `except`. Filtrar no call site deixaria passar exatamente a exceção que carrega nome | `Formatter` customizado (não vê `args`); sanitizar em cada `except` (cobertura impossível de garantir) | 🟡 |
| D-06 | A auditoria é emitida **na borda** (`src/app.py`), nunca no caso de uso nem no núcleo | IP e identificador de requisição são HTTP; levar isso para dentro obrigaria o núcleo a conhecer a borda, que é o que o `ADR-24`/`ADR-25` proibiram | auditar dentro dos casos de uso, recebendo IP por parâmetro | 🟢 |
| D-07 | `ResultadoDeUpload` ganha o campo `desfecho` (`novo` / `identico` / `substituido`) | A borda precisa distinguir os três casos da `RN-17` para auditar, e reinferi-los pelo texto da mensagem daria autoridade semântica ao literal — o que a `RF-20` proíbe | comparar a mensagem na borda; reconsultar a porta | 🟢 |
| D-08 | A identificação do arquivo na auditoria usa `decompor_nome_armazenado` (`utils/validate.py:152`) mais a extensão | A autoridade que separa chave de rótulo já existe e é testada; duplicar a regra criaria a segunda cópia que o projeto já pagou caro | fatiar a referência com `split("__")` no ponto de auditoria | 🟢 |
| D-09 | A medição entra em `CarregadorDeArvoresGedcom.carregar`, não em cada chamador | É o ponto único onde o parse acontece, e é o mesmo ponto que o cache da feature 047 intercepta | medir em `app.py` (mediria o caminho todo, não o parse) | 🟢 |
| D-10 | O log geral rotaciona por tamanho (5 × 5 MB); a **auditoria grava um arquivo por dia e não descarta** | Rotação por tamanho na auditoria apagaria dado antes dos 90 dias que a `RN-10` declara — o sistema passaria a expurgar sozinho, contra a decisão | rotação por tamanho também na auditoria; arquivo único sem rotação | 🟡 |
| D-11 | Pasta de log inescrevível degrada para **console apenas**, com um único aviso, e nunca derruba requisição | É o caso do container sem volume montado: a aplicação precisa subir e servir, e a falha precisa ser visível | abortar a subida (derruba o container por um problema de pasta) | 🟡 |
| D-12 | A linha de acesso do `waitress` sobe para `WARNING`; a nossa passa a ser a única linha por requisição | Duas linhas por requisição no console, sem diferença informativa, só atrapalham a leitura de quem opera | manter as duas; remover o handler inteiro do `waitress` (perderia os erros dele) | 🟡 |
| D-13 | O `print` de inicialização vira `INFO` no logger do módulo, com o mesmo texto | Muda o destino, não o conteúdo: a linha que diz endereço e threads continua legível no console | remover a linha (perde a única prova do endereço em uso) | 🟢 |
| D-14 | Nenhum arquivo de `src/` fora de `utils/logs.py`, `utils/auditoria.py`, `web/hooks_de_registro.py`, `app.py`, `ports/adaptadores.py` e `application/upload_gedcom.py` é tocado | Mantém o delta auditável e respeita a direção de dependência já vigente | espalhar chamadas de auditoria nos casos de uso | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` está com zero marcadores `[DÚVIDA]` — as três dúvidas foram resolvidas
na sessão de esclarecimentos de 2026-10-25 e estão registradas em `requirements.md` §9.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `utils/logs.py` | `_reversa_sdd/architecture.md#3` (pacote `utils/`, folha) | `componente-novo` | Configuração dos três destinos, contexto de requisição, máscara e `medir()` |
| `utils/auditoria.py` | `_reversa_sdd/architecture.md#3` | `componente-novo` | Linha de auditoria tipada: ação, desfecho, chave+extensão, contagens, IP, identificador |
| `web/hooks_de_registro.py` | `_reversa_sdd/c4-components.md` (borda HTTP) | `componente-novo` | `before_request` (identificador), `after_request` (cabeçalho + linha de acesso) |
| `app.py` — três mensagens | `_reversa_sdd/domain.md#5` | `contrato-alterado` | Prefixo mantido, `{e}` trocado por "O detalhe foi registrado no log." |
| `app.py` — cinco fluxos | `_reversa_sdd/c4-components.md` | `regra-alterada` | Upload, substituição, aposentar (2), DNA e busca passam a auditar |
| `app.py` — `__main__` | `_reversa_sdd/architecture.md#2` | `regra-alterada` | `print` de inicialização vira linha de log |
| `ports/adaptadores.py` — carregador | `_reversa_sdd/c4-components.md` | `regra-alterada` | `carregar` mede o parse com `medir("carregar_arvore")` |
| `application/upload_gedcom.py` | `_reversa_sdd/upload-gedcom/design.md` | `contrato-alterado` | `ResultadoDeUpload` passa a expor `desfecho` |
| RNF "Observabilidade" das 5 units | `_reversa_sdd/*/requirements.md#requisitos-não-funcionais` | `regra-removida` | A afirmação "nenhum log" deixa de valer (convergência no `/reversa-sync`) |
| Operação | `_reversa_sdd/c4-containers.md` | `contrato-novo` | Pasta de log, volume da auditoria, rotação do orquestrador |

## 6. Delta no modelo de dados

- Resumo: **nenhuma tabela, nenhuma coluna, nenhuma migração.** A persistência Postgres não é
  tocada — inclusive a tabela `access_audit` do sistema alvo (`_reversa_sdd/migration/target_data_model.md`)
  **não** é usada aqui, porque a auditoria não pode desaparecer quando `DATABASE_URL` está ausente.
  Entram duas estruturas **em memória**: o contexto de requisição (um slot) e a linha de auditoria
  (campos), mais o campo `desfecho` em `ResultadoDeUpload`.
- Detalhe completo em: `_reversa_forward/049-sistema-de-log/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Cabeçalho `X-Request-ID` em toda resposta, e as três mensagens de erro de tela | HTTP | `_reversa_forward/049-sistema-de-log/interfaces/http.md` |

## 8. Plano de migração

1. Não há migração de dado. Instalação nova cria a pasta de log no arranque, como já faz com a
   pasta de upload.
2. Instalação existente (Windows local): a pasta é `logs/` ao lado de `src/`, ou o caminho de
   `ANALISADOR_LOG_DIR`. Nada a fazer além de rodar.
3. Container: acrescentar o volume `./logs:/app/logs` e a rotação `json-file` no compose. Sem o
   volume, a auditoria cai para console e a degradação é avisada uma vez (`D-11`).
4. `.gitignore`: a linha da pasta de log **precisa do operador** — o caminho não está no
   `allowedPaths` de `.reversa/reversa-config.json` e a escrita é recusada por política.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A máscara não alcançar o traceback e o nome escapar justamente na exceção | alto | alta | teste dedicado com exceção que carrega nome, e-mail e ID de kit (`D-05`); a asserção é sobre o texto formatado final, não sobre `record.msg` |
| Handlers duplicados por `create_app()` chamado muitas vezes | médio | alta | guarda de idempotência (`D-01`) mais teste que conta handlers |
| A máscara mascarar demais e cegar o diagnóstico | médio | média | dois padrões só (ID de kit e e-mail), ambos com forma fechada; nada de heurística por palavra |
| A mudança de mensagem quebrar paridade | baixo | baixa | o harness classifica por `modo()` a partir do prefixo (`harness.py:185`); o prefixo é preservado de propósito |
| Custo do filtro e da formatação no caminho quente | baixo | média | uma linha por evento, sem serialização; medição do parse já existe (`D-09`) |
| Pasta não gravável no container sem volume | médio | média | `D-11`: console apenas, um aviso, serviço continua |
| A trilha de auditoria crescer sem expurgo | médio | certa | `RN-10`: prazo declarado; `D-10` não descarta por tamanho; o expurgo manual está registrado como lacuna 🟡 no requirements |
| `.gitignore` fora do `allowedPaths` bloquear a ação de versionamento | alto | certa | o operador libera o caminho antes do coding, ou a ação é marcada como bloqueada e registrada |

## 10. Critério de pronto

- [ ] Os três destinos existem e a auditoria não propaga para os outros dois
- [ ] Toda resposta traz `X-Request-ID`, e a linha de acesso e a de erro carregam o mesmo valor
- [ ] Aposentar audita sucesso **e** falha, e o teste dos dois desfechos passa
- [ ] O teste de privacidade roda a análise com fixture sintética e nenhum nome aparece no log capturado
- [ ] A máscara alcança o traceback (teste com exceção que carrega nome)
- [ ] As três mensagens de tela terminam em "O detalhe foi registrado no log." e o traceback está no log
- [ ] `medir("carregar_arvore")` registra milissegundos
- [ ] Container escreve no fluxo padrão, com rotação declarada, e a auditoria vai para o volume
- [ ] Suíte verde a partir do marco de 1656 passam / 9 pulados, e paridade 100 %
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado
- [ ] Decisão de observabilidade registrada e RNF das 5 units convergidas no `/reversa-sync`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-25 | Versão inicial gerada por `/reversa-plan` | reversa |
