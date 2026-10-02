# Plano de tratamento: BUG-20260929-BJJH

**Estado: proposta, nenhum código alterado.**
Severidade `critical`, prioridade `P0`, `visibility: restricted`.
Escrito em 2026-10-02, depois de reler o registro, a evidência de código e as oito specs citadas.

---

## 1. O que este plano não é

Não é o plano da correção do `BJJH` no aplicativo legado. Ao ler as specs, ficou claro que o
critério de aceite deste bug **não é satisfazível no legado**, e isso precisa ser dito antes de
qualquer orçamento de esforço.

## 2. A descoberta central

O segundo critério de aceite diz:

> Requisição que referencie árvore de outro dono responde `404` (não `403`), conforme
> `_reversa_sdd/migration/risk_register.md#risk-005`.

O legado **não tem autenticação, nem sessão de usuário, nem `owner_id`** em nenhum ponto do
projeto. Verificado de novo agora: nenhuma ocorrência de `login`, autenticação, sessão ou
`owner_id` em `analisador-genealogico/`, e nenhuma ocorrência de `owner`, `isolamento`, `tenant`,
`session` ou `404` em `tests/`. O `app.secret_key` existe em `app.py:11`, mas nenhuma sessão é
criada ou validada.

Sem identidade, **não existem "dono A" e "dono B"** para que a resposta seja 404 em vez de 403.
O critério não é difícil no legado: é inaplicável. A própria spec confirma isso, ao dizer que o
comportamento esperado "está definido na spec efetiva, **não no código atual**".

E o `RISK-005` nomeia o plano de contingência, que também é uma decisão:

> se o isolamento não puder ser garantido estruturalmente na Onda 3, **não liberar a Onda 4** —
> manter a aplicação single-tenant até o isolamento ser provado.

Ou seja: a spec já previu exatamente a situação em que estamos, e já escreveu a saída aceitável,
que é **manter single-tenant**, não remendar o legado.

## 3. O que o refactor mudou neste quadro

Duas correções de fato, que importam para não se trabalhar sobre premissa morta.

**O "artefato HTML em caminho fixo" não existe mais.** Era o Problema 1 do intake e a razão
original de eu ter chamado este bug de urgente. A transformação `OPP-20260929-SEQO` removeu o
`STATIC_FOLDER`, e `app.py` hoje não cria `static/`. O que resta, e sustenta o bug, é o estado
global em memória mais a pasta `uploads/` compartilhada.

**O estado global depende de mutação in-place.** `upload.py:15-19` declara `people`, `families`,
`graph` e `child_to_family`. `upload.py:95-98` grava por `clear()` mais `update()` justamente para
que as referências importadas por outros módulos continuem válidas, e o comentário do autor
registra que isso é deliberado. Como `graph` é reatribuído, `path_finding.py:38` o importa dentro
da função, enquanto `people` é importado no topo de cinco módulos. **Qualquer versão de escopo por
dono exige refatorar os pontos de acesso em cerca de onze locais**, não trocar um dicionário.

## 4. Duas divergências de rastreabilidade encontradas

Declaro porque afetam a confiança no registro, e não são minhas para consertar em silêncio.

| Locator | Diz | Estado real |
|---|---|---|
| `evidence/verificacao-codigo.md:38-44` | `app.py:13-16` tem `STATIC_FOLDER` | O arquivo não tem mais. A própria linha 42 da citação está morta |
| `risk_register.md:67` | state global em `app.py:20-23` | Hoje vive em `reconstructed/upload.py:15-19` e `:95-98` |

A verificação de código é de 2026-09-29 e foi feita antes das transformações de refactor. O
`bug.md:113-116` já corrigiu parte disso; a evidência e o `risk_register` ficaram para trás.

## 5. As três rotas

### Rota 1. Aceitar o risco e manter single-tenant

**O que é.** Não mexer no código. Registrar no bug que a correção é estrutural e pertence à Onda 3,
com o aceite de risco residual no nome de Adriano, que é o owner que o `RISK-005` já define.

**Custo.** Uma alteração de registro, sem tocar em código.

**Ganha.** Nada de código de isolamento escrito em cima de uma arquitetura que a migração vai
substituir. Nada de trabalho jogado fora na Onda 3.

**Custo real.** O bug permanece `open` e o `P0` continua aberto. O legado fica utilizável apenas
por uma pessoa por vez, o que é verdade hoje de qualquer forma porque ele nunca foi deployado
(`cutover_plan.md:23`: "não há produção a parar", "não há usuários ativos").

**Pré-requisito honesto.** A aplicação não pode ser exposta a mais de uma pessoa enquanto isso.

### Rota 2. Mitigar com escopo por sessão em memória

**O que é.** Implementar a **Opção 2** do `BR-HUMANA-004`. `{session_id: tree}` com trava. Um
dicionário de árvores por sessão do Flask, e os pontos de acesso passando a resolver a árvore da
sessão corrente em vez de lerem o global.

**Custo.** Alto. Toca `upload.py`, `app.py` e os cerca de onze pontos de acesso listados na seção 3.
Exige teste negativo novo. Exige decidir se o cookie de sessão anônima é aceitável como identidade
para dado genético.

**Ganha.** Duas sessões simultâneas deixam de compartilhar árvore. Atende ao **primeiro** e ao
**quarto** critérios de aceite.

**O que não ganha, e isto é decisivo.** Não atende ao segundo critério. Sessão anônima não é dono:
não há autenticação, então continua não existindo "recurso de outro dono" para responder 404. O bug
não fecha. A própria spec marca esta opção como **não recomendada**, e diz que a entrada existe
"para dar ao usuário a chance de vetar o custo, não porque a alternativa seja recomendável".

**Risco de fazer.** A Onda 3 vai eliminar este código. Escrever isolamento defensivo agora, para
depois substituí-lo por isolamento estrutural, é o cenário que o `risk_register.md:180` chama de
"o pior dos dois mundos".

### Rota 3. Tratar na Onda 3, junto do alvo

**O que é.** Manter o bug registrado como bloqueio de Onda 3 e resolvê-lo onde a spec manda:
`api/auth` resolvendo `owner_id`, `ports/tree_repository.py` com escopo obrigatório na assinatura,
`owner_id` como invariante do aggregate em `NOT NULL`, e o teste negativo de 404 que o
`cutover_plan.md:33` exige como portão de go-live.

**Custo.** Zero no legado. É o custo que a migração já orçou na Onda 3.

**Ganha.** O critério de aceite inteiro, incluindo o 404, porque passa a existir identidade.

**Custo real.** O bug fica aberto até a Onda 3 existir. Depende da Onda 3 acontecer, e o
`RISK-008` registra que o projeto "pode progredir indefinidamente sem atingir cutover".

## 6. Comparação

| | Rota 1 | Rota 2 | Rota 3 |
|---|---|---|---|
| Toca código do legado | não | sim, extenso | não |
| Fecha o bug | não | não | sim |
| Atende critério 1 (sessões não compartilham) | não | sim | sim |
| Atende critério 2 (404, não 403) | não | não | sim |
| Trabalho perdido na Onda 3 | nenhum | todo | nenhum |
| Exige decisão humana | aceite de risco | sim, e de identidade | não |

## 7. Recomendação

**Rota 3, com o registro da Rota 1 como estado provisório declarado.**

As duas coisas juntas: o bug continua `open` e bloqueando a Onda 3, e o registro passa a dizer
explicitamente que o legado é **single-tenant por contingência já prevista no `RISK-005`**, não por
descuido. Isso é o que a spec já decidiu, e é o único caminho em que o critério de aceite fecha
inteiro.

A Rota 2 só se justifica se existir uma necessidade concreta de mais de uma pessoa usar o
aplicativo **antes** da Onda 3. Nesse caso ela compra o critério 1, e o preço é código que a Onda 3
descarta.

## 8. Perguntas que eu não posso responder sozinho

1. Alguém além de você precisa usar esta aplicação antes da Onda 3? É isto que decide entre a
   Rota 2 e as Rotas 1 e 3.
2. A Onda 3 está no horizonte, ou o projeto está parado na Onda 1?

## 9. O que eu não fiz

Nenhum arquivo de código foi tocado. Nenhuma spec foi alterada. As divergências da seção 4 estão
declaradas e não corrigidas, porque corrigir spec é ato humano.

---
*Plano escrito por agente em 2026-10-02. Não é correção: correção é trabalho do
`/reversa-debugger-fix`, em dois gates de aprovação.*
