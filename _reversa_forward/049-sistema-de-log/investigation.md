# Investigação: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Documento de apoio ao `roadmap.md` — o que foi pesquisado, o que foi descartado e o que **não**
> foi medido.

## 1. O que já existe no legado

Medido nesta sessão por varredura de `src/`:

| Onde | O que é | Quantidade |
|---|---|---|
| `src/app.py` | `current_app.logger.warning` (recusa de `Host`), `current_app.logger.exception` (GEDCOM ilegível, envio, análise, busca) | 5 chamadas |
| `src/ports/adaptadores.py` | `_log.info` de acerto/reconstrução do cache de árvores e `_log.warning` de capacidade inválida | 4 chamadas |
| `src/app.py:777` | `print` com endereço e número de threads | 1 |
| configuração | **nenhuma** — não há `basicConfig`, `dictConfig` nem `setLevel` em `src/` | 0 |
| destino | o handler de último recurso do `logging`, que escreve `WARNING` e acima no `stderr` | implícito |

Consequência medida: **tudo abaixo de `WARNING` se perde**, não há arquivo, não há identidade de
requisição e não há auditoria. O `_log.info` do cache (feature 047) é um caso concreto: existe,
custa nada e não chega a lugar nenhum.

## 2. Alternativa 1 — ferramenta externa de observabilidade

**Descartada.** Três motivos, em ordem de peso:

1. **Dado sensível.** O sistema trata árvore genealógica de pessoas vivas. Enviar linha de log a um
   coletor externo é exportar dado pessoal para fora da máquina do operador, e o Princípio I proíbe
   justamente o caminho do log.
2. **Escala.** Um operador, um processo, uma tela. A ferramenta traria servidor, agente e painel
   para uma base de linhas medida em milhares por dia, não por segundo.
3. **Dependência.** `RN-09` fixou: nenhuma dependência nova de runtime. O `requirements.txt` é lista
   de runtime e o container não tem coletor.

O plano anexado chegou à mesma conclusão; esta investigação apenas registra o porquê.

## 3. Alternativa 2 — biblioteca de log estruturado de terceiro

**Descartada pelo mesmo motivo da `RN-09`**, e com um contra próprio: ela resolveria formatação e
contexto, mas **não** resolveria a máscara no traceback, que é o requisito caro desta feature
(`D-05`). O que ela entregaria de graça — formato de chave=valor — cabe em vinte linhas.

## 4. Alternativa 3 — `basicConfig`

**Descartada.** `basicConfig` é no-op a partir da segunda chamada no mesmo processo. A suíte importa
e cria a aplicação centenas de vezes: o primeiro teste configuraria, todos os outros herdariam a
configuração do primeiro — inclusive caminhos e níveis. É o pior modo de falha possível, porque
passa no teste isolado e falha na ordem real.

## 5. Alternativa 4 — `dictConfig`

**Descartada para esta entrega, não para sempre.** Traz configuração declarativa e recarga, ao custo
de um dicionário de estrutura rígida para três destinos. O plano anexado diz que o protótipo usou
configuração imperativa e que a migração "deve ser validada antes de entregar" — validar isso custa
mais do que a feature inteira. Fica registrado como caminho de evolução se o número de destinos
crescer.

## 6. Alternativa 5 — usar a linha de acesso do servidor

**Descartada.** O `waitress` já registra uma linha por requisição no nível informativo, e ela é
suficiente para "quem chamou o quê". Não serve para o requisito porque:

- não carrega identificador que ligue a linha de erro ao acesso;
- não passa pelo nosso formatter, então não passa pela máscara;
- o formato é do servidor, e o operador não controla o nível por módulo.

Decisão derivada (`D-12`): ela sobe para `WARNING` para não duplicar o console, e os erros dele
continuam visíveis.

## 7. Alternativa 6 — auditar no banco

**Descartada, e o registro importa.** O DDL do sistema alvo já prevê uma tabela `access_audit`
(`_reversa_sdd/migration/target_data_model.md`), e `_reversa_sdd/migration/data_migration_plan.md`
a marca como "novo, sem origem". Ou seja: existe um lugar natural para auditoria persistida **no
alvo**. Não é aqui porque:

- a persistência é **opcional** (`ADR-27`): sem `DATABASE_URL` o registrador é nulo, e uma auditoria
  que desaparece quando o banco está desligado não é auditoria;
- o driver não está no `.venv` oficial (`L-26`), então nem seria possível testar o caminho de escrita;
- `access_audit` é estrutura do alvo, e criar a tabela aqui inverteria a direção da migração.

## 8. Padrões aplicados

| Padrão | Onde | Por que este |
|---|---|---|
| Contexto implícito por `contextvars` | `D-03` | Sobrevive à requisição sem parâmetro novo em assinatura nenhuma, e não vaza entre threads do pool |
| Chave de correlação devolvida ao cliente | `D-04` | É o que transforma "deu erro" em "deu erro nesta requisição": o operador copia o cabeçalho |
| Redação por filtro no destino | `D-05` | Cobre 100 % das linhas, inclusive as que ainda não existem; sanitizar no call site cobre só as de hoje |
| Rotação por tamanho no diagnóstico, por tempo na auditoria | `D-10` | São públicos diferentes: o diagnóstico é descartável, a auditoria é prova com prazo declarado |
| Degradação graciosa do destino | `D-11` | Diagnóstico não pode ser motivo de indisponibilidade |

## 9. O que **não** foi medido

Registrado para não virar promessa:

- **Custo do filtro e da formatação** por linha. A estimativa é de microssegundos, e nenhuma medição
  foi feita porque o gargalo conhecido do sistema é o parse (~20,9 s,
  `_reversa_sdd/gaps.md#34-custo-medido-nesta-rodada`).
- **Comportamento sob 4 threads escrevendo no mesmo arquivo.** O `logging` é thread-safe por
  construção do handler, e não há medição de contenção.
- **Custo de disco** da trilha de auditoria em uso real: sem expurgo automático (`RN-10`), o número
  depende do operador.
- **A forma exata do traceback mascarado** — o plano anexado declara explicitamente que a parte de
  privacidade "ainda não foi testada em protótipo". É o item de maior incerteza técnica da feature,
  e é por isso que ele tem teste próprio (`D-05` + critério de pronto).

## 10. Fontes

- `_reversa_sdd/tela-de-entrada/requirements.md#requisitos-não-funcionais` — o único log da unit.
- `_reversa_sdd/analise-dna/design.md#observabilidade` — "nenhum log estruturado".
- `_reversa_sdd/questions.md#pergunta-14` — as três saídas e a recomendação.
- `_reversa_sdd/gaps.md#5-fechadas-nesta-rodada--21-lacunas` — decisão 14, "Agendado".
- `_reversa_sdd/parity/harness.py:161-189` — `modo()`, a classificação por prefixo que protege a
  paridade da mudança de mensagem.
- `_reversa_sdd/migration/target_data_model.md` e `data_migration_plan.md` — `access_audit` do alvo.
- `.reversa/principles.md#i` e `#ii`.
- `tests/test_cache_de_arvores.py:265-279` — precedente do teste de privacidade no log.
