# Roadmap: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature fecha a distância entre o topo e os cartões de resultado em **quatro frentes de
apresentação**: os alertas de retorno passam a usar a paleta (hoje são a única cor fora dela na
primeira dobra); a ação principal deixa de ser uma barra verde de largura total no desktop; o `h1` e a
arte do topo descem um degrau de escala; e o comentário do template que descreve a introdução como
"alinhada à esquerda" é corrigido para descrever o arranjo real da `RN-24` (centralizado e estreito).
O ritmo entre os blocos do topo é conferido, sem tocar nos cartões.

A descoberta que mudou o escopo: a introdução centralizada **não é defeito** — é a `RN-24`, pedida pelo
operador em 2026-10-10 e presa por `test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita`.
O defeito é só o **comentário** que ficou para trás. A feature não reabre a `RN-24` e não mexe no
alinhamento.

A mudança toca **um comentário no template** e a **folha de estilo**. O rodapé (cartões, selo de cM,
espaçamentos) fica intocado por decisão (`RN-08`). O documento servido muda, então o `SHA_DA_TELA` é
movido na mesma rodada e a mudança é declarada no adendo.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Nenhum dado é lido: o objeto é a folha e um comentário do template | respeita |
| II. Comportamento observável é preservado em refatoração | Nenhuma cor efetiva dos selos, nenhum texto e nenhuma rota mudam; o rodapé fica idêntico (`RN-08`); a `RN-24` fica idêntica | respeita |
| III. Nenhuma mudança sem teste que a cubra | As guardas existentes cobrem: `test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita` (RN-24), `TestOContrasteDosSelos`, o hash da tela e a ordem da masthead. Os quatro testes entram na verificação | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhuma travessia ou cálculo de parentesco é tocado | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhuma faixa de cM ou limiar é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O escopo de arquivos é **`src/assets/app.css` + um comentário em `src/templates/index.html`** | O comentário da introdução é o único texto de código em contradição com a `RN-24`; o resto é folha. `git diff --stat` deve listar só esses dois arquivos | (a) mexer no markup da introdução — revogaria a `RN-24`; (b) corrigir só a folha e deixar o comentário falso — mantém a armadilha que gerou este pedido | 🟢 |
| D-02 | A introdução **não** é tocada: nem markup, nem alinhamento, nem coluna | A `RN-24` e `tests/test_banner_do_topo.py:270-298` prendem o arranjo; o comentário passa a descrevê-lo. Qualquer mudança de alinhamento é outra feature, com revogação declarada | (a) alinhar à esquerda — quebra o teste e a decisão do operador; (b) sobrepor por CSS — o teste continuaria verde, mas a intenção seria desfeita em silêncio | 🟢 |
| D-03 | Os alertas `.alert-success` e `.alert-danger` são tematizados **na folha**, sem mudar o markup, com quatro tokens novos e contraste medido | O markup já tem as classes certas; o que falta é a regra. Escopo restrito a essas duas classes para **não** alcançar o `.alert-warning` do cartão de DNA (`index.html:1015`), que está no rodapé e não pode mudar (`RN-08`) | (a) trocar o alerta por um componente próprio — mais markup e um componente novo para uma caixa de mensagem; (b) usar só `--aviso-bg` — borraria a diferença entre sucesso e perigo | 🟢 |
| D-04 | Tokens novos: `--sucesso-bg`, `--sucesso-line`, `--perigo-bg`, `--perigo-line`, definidos nos dois temas; o texto usa `--ink` | Medido: claro `--ink` sobre `#EDF4E6` = **13,70:1** e borda `#3F6B2E` = **5,57:1**; perigo `#FBEDEA` = **13,49:1** e borda `#A8321F` = **5,86:1**; escuro `#1E2A17` = **12,16:1** e borda `#8DBB6E` = **6,77:1**; perigo `#2E1B18` = **13,22:1** e borda `#EE9A88` = **7,47:1**. A borda atual é 1,15:1 | (a) reaproveitar `--aviso-bg`/`--aviso-line` — confunde aviso com sucesso; (b) manter o verde padrão do framework — é o defeito que a feature corrige | 🟢 |
| D-05 | O botão de fechar do alerta **permanece** e é só ajustado (opacidade e tamanho); o ícone continua o do framework, que já se inverte no tema escuro | A decisão 4a preserva o comportamento; recriar o ícone seria markup novo sem ganho. A verificação inclui olhar o X nos dois temas | (a) remover o botão — muda comportamento; (b) trocar o ícone por SVG próprio — mais markup e mais um ativo para manter | 🟢 |
| D-06 | A ação principal ganha largura natural acima de 576 px via CSS (`.d-grid > .btn`), e continua de largura total abaixo | Os três formulários usam o mesmo `d-grid` (medido: três ocorrências), então uma regra cobre os três. A pílula fica reservada às ações secundárias do resultado; o CTA principal mantém o raio de cartão (10 px) e uma altura menor | (a) trocar `d-grid` por `d-flex` no markup — três edições para o mesmo efeito; (b) transformar o CTA em pílula — inverteria a hierarquia (primário igual a secundário) | 🟢 |
| D-07 | A escala do topo desce: `h1` em `clamp(1.8rem, 3.2vw, 2.2rem)` e arte em `min(50%, 280px)` | O topo salta de 2,5rem para 1rem; 2,2rem mantém o título como maior elemento e reduz o "buraco" branco. A arte a 280 px preserva a presença sem dominar a primeira dobra | (a) manter 2,5/320 — não resolve o peso; (b) descer para 2rem — aproxima o título dos títulos de cartão e perde hierarquia | 🟢 |
| D-08 | O ritmo do topo é **verificado**, não reescrito: medir os degraus (1rem dos campos, 1.5rem das abas e da masthead, 1.5rem do bloco de observações) e só ajustar o que estiver fora | A `RN-08` proíbe mexer no rodapé, e o topo não mostrou um degrau claramente errado além da transição para o resultado. A entrega registra a medição; se nada estiver fora, nada muda | (a) reescrever todos os espaçamentos — churn sem medição; (b) ignorar o `RF-05` — deixa a verificação sem registro | 🟡 |
| D-09 | O `SHA_DA_TELA` é recalculado e o comentário do hash recebe um bloco datado explicando a contribuição | É a praxe do arquivo: o hash mede "a tela não mudou sem declaração", e a mudança do comentário entra nele. A declaração completa fica no adendo do `/reversa-sync` | (a) trocar o valor sem explicar — o comentário perde o valor de trilha; (b) não atualizar — a suíte falha | 🟢 |

## 4. Premissas

Nenhuma premissa vem de marcador em aberto: o documento chegou ao plano com **0** marcadores, depois da
sessão de esclarecimento e da correção de escopo da `RN-24` (`requirements.md` §9).

| Premissa | Origem (`requirements.md`) | Risco se errada |
|----------|----------------------------|-----------------|
| n/a | — | — |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Comentário da masthead | `src/templates/index.html:185-187`; `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md#3-regras-novas-que-a-feature-cria` | regra-alterada (documentação) | O comentário passa a descrever a `RN-24` (centralizado e estreito); nenhum markup muda |
| Folha de estilo da tela | `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md`; `src/assets/app.css` | regra-alterada (apresentação) | Alertas na paleta, CTA natural no desktop, escala do topo, ritmo verificado |
| Rota `GET /app.css` | `src/app.py:472-490` | **sem mudança** | Mesmo `GET`, `text/css`, `ETag`/`304`, `404` sem corpo |
| Template `index.html` (markup) | `src/templates/index.html:190-228` | **sem mudança** | A `RN-24` fica intacta: `row justify-content-center` + `col-lg-*`, sem `text-start` |
| Cartões de resultado | `index.html:538-640`; `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` | **sem mudança** | Nenhuma cor, selo ou espaçamento dos cartões muda (`RN-08`) |
| Testes da tela | `tests/test_banner_do_topo.py`, `tests/test_estilo_da_tela.py`, `tests/test_icone_de_atalho.py` | **sem mudança**, exceto o valor do `SHA_DA_TELA` | Nenhum teste removido; o teste da `RN-24` continua verde; o hash é atualizado |

## 6. Delta no modelo de dados

- **Nenhum dado de domínio, payload, tabela ou migração.** O delta é de apresentação: quatro tokens de
  alerta entram e duas regras de escala mudam.
- Detalhe completo em: `_reversa_forward/027-harmonizar-topo-da-tela/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo muda. O HTML servido em `GET /` tem o mesmo texto e a mesma estrutura; o
`/app.css` mantém método, `Content-Type`, `ETag`, `304` e `404`. Por isso **não há diretório
`interfaces/`**.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a — nenhum contrato HTTP, de arquivo ou de banco afetado | — | n/a |

## 8. Plano de migração

Não há migração de dados. A ordem de execução existe para não perder a linha de base do hash e da
suíte.

1. **Congelar a linha de base** (`D-09`): `git status`, `git log -1`, suíte completa (esperado
   1.048/9) e o `sha256` atual de `GET /`.
2. **Tematizar os alertas** (`D-03`, `D-04`, `D-05`): tokens novos, regras de `.alert-success`,
   `.alert-danger` e do `btn-close`, com os números medidos no comentário.
3. **Aliviar a ação** (`D-06`): regra de `.d-grid > .btn` na media query de 576 px.
4. **Compactar a escala** (`D-07`): `h1` e arte.
5. **Corrigir o comentário** (`D-01`, D-02): descrever a `RN-24`, sem tocar no markup.
6. **Verificar o ritmo** (`D-08`) e registrar a medição.
7. **Rodar os três arquivos de teste**, a suíte completa e conferir que o teste da `RN-24` segue verde.
8. **Medir o `sha256`** de `GET /` e atualizar o `SHA_DA_TELA` **se** ele mudar; como o comentário é
   Jinja, a expectativa é que não mude (`D-09`).
9. **Declarar** no adendo da feature, no `/reversa-sync` (`RF-08`).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Tocar no markup da introdução por engano ao editar o comentário vizinho | alto — quebra a `RN-24` e o teste | média | `D-02` proíbe; o teste `test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita` roda na verificação |
| A regra do alerta alcançar o `.alert-warning` do cartão de DNA | médio — muda o rodapé, que deve ficar intocado | média | `D-03` restringe a `.alert-success` e `.alert-danger`; nenhum seletor `.alert` genérico |
| O X do alerta sumir no tema escuro | médio — perde a ação de fechar | média | `D-05` mantém o ícone do framework, que se inverte no escuro; o onboarding manda olhar os dois temas |
| O novo `h1` perder hierarquia em telas estreitas | baixo — o título deixa de ser o maior elemento | baixa | O piso do `clamp` é 1,8rem, acima do título de cartão (1,2rem) |
| Atualizar o hash sem explicar a contribuição | médio — o comentário perde a trilha | baixa | `D-09`: bloco datado com a contribuição de cada mudança |
| A regra `.d-grid > .btn` alcançar outro grid | baixo — não há outro `d-grid` no template | baixa | Medido: três ocorrências, todas de formulário |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `git diff --stat` lista **apenas** `src/assets/app.css` e `src/templates/index.html` (`D-01`)
- [ ] A introdução continua com `row justify-content-center` + `col-lg-*`, sem `text-start` (`RN-24`)
- [ ] O alerta de sucesso e o de erro usam os tokens novos, com os quatro contrastes no comentário (`RF-02`, `RF-10`)
- [ ] O botão de ação não ocupa a largura do cartão acima de 576 px e continua total abaixo (`RF-03`)
- [ ] `h1` ≤ 2,2rem e arte ≤ 280px (`RF-04`)
- [ ] Nenhuma regra dos cartões de resultado mudou (`RN-08`)
- [ ] Suíte verde com **1.048 passam / 9 pulados** e o teste da `RN-24` verde (`RF-09`)
- [ ] `SHA_DA_TELA` verificado: o comentário é Jinja, o HTML não muda e o hash permanece `c4a34f7b…` (`RF-08`)
- [ ] Adendo `027` escrito no `/reversa-sync`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-17 | Versão inicial gerada por `/reversa-plan`, já com a correção de escopo da `RN-24` | reversa |
| 2026-10-17 | Correção durante o coding: o comentário é Jinja, o HTML servido não muda e o `SHA_DA_TELA` permanece `c4a34f7b…` | reversa |
