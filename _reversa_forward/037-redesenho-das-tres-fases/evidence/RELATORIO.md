# Relatório da entrega: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Ações executadas: **28 de 28**

## 1. O que o operador encontra

A tela de entrada tem **três fases numa barra lateral**: `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM` e `3. Analisador de DNA`. As abas horizontais não existem mais.

- **Fase 1** — cabeçalho `Fase 1 — Árvores GEDCOM`, caixa "Árvore atualmente aberta" (com o link `escolher outra árvore`), **dois contadores** (árvores armazenadas e disponíveis), a tabela de sempre com linhas alternadas e ações empilhadas, e o bloco de envio com o nome do arquivo escolhido.
- **Fase 2** — os dois campos de pessoa e a ação na mesma linha, com sugestões de nome.
- **Fase 3** — o bloco do CSV e o bloco do nome, com a ação destacada.
- **Sem árvore aberta**, as fases 2 e 3 não oferecem campo: mostram um estado vazio que aponta para a fase 1.
- **Combobox**: digitar filtra os nomes da árvore, as setas percorrem, `Enter` escolhe, `Esc` fecha; o texto digitado continua livre e é ele que a busca recebe.

## 2. Cobertura dos requisitos

| RF | Situação | Onde |
|---|---|---|
| RF-01 três fases | **testado** | `test_a_tela_tem_uma_barra_com_tres_fases` |
| RF-02 fase 1 com lista e envio | **testado** | `test_a_fase_1_tem_a_lista_e_o_envio_*` |
| RF-03 fase 2 só com os campos | **testado** | `test_a_fase_2_tem_so_os_dois_campos` |
| RF-04 fase 3 com CSV e nome | **testado** | `test_a_fase_3_tem_o_csv_e_o_nome` |
| RF-05 fases 2 e 3 sem campo | **testado** | `test_as_fases_2_e_3_nao_oferecem_campo_sem_arvore` |
| RF-06 fase 2 ativa após abrir | **testado** | `test_com_arvore_a_fase_2_esta_ativa` |
| RF-07 cabeçalho e caixa de status | **parcial** — a fase 1 e a fase 2 têm teste; a caixa da fase 3 não |
| RF-08 ação junto do campo | **sem teste** — CSS (`linha-de-campos`, `.campo-da-acao`) |
| RF-09 tabela listrada e ações maiores | **parcial** — colunas, botões e literais têm teste herdado; o listramento e o empilhamento são CSS sem teste |
| RF-10 retorno do arquivo escolhido | **sem teste** — JS de ~10 linhas |
| RF-11 botão de tema | **testado** (herdado) — `aria-pressed` e persistência continuam cobertos |
| RF-12 literais preservados | **testado** | `test_os_rotulos_congelados_continuam` |
| RF-13 navegação por teclado | **parcial** — `aria-selected` e a existência do handler têm teste; a execução não |
| RF-14 320 px sem rolagem | **sem teste** — sem navegador no projeto |
| RF-15 combobox | **parcial** — estrutura, ARIA e segurança do JSON testados; comportamento executado no checklist manual |
| RF-16 contadores | **testado** | `test_os_contadores_contam_o_que_existe` |

**Resumo:** 8 testados de ponta a ponta, 4 parciais, 4 sem teste automatizado (3 deles por ausência de navegador/executor de JS), 1 herdado.

## 3. Medições

| | Antes | Depois |
|---|---|---|
| Suíte | 1309 passam, 11 pulados | **1334 passam, 11 pulados** |
| `GET /` vazio | 30.781 bytes, `c4a34f7b…` | **38.484 bytes, `794711aa…`** |
| Testes novos | — | 25 (16 + 9) |
| `src/assets/app.css` | — | +299 linhas |
| `src/templates/index.html` | — | +627/−169 |
| `tests/test_icone_de_atalho.py` | — | +9/−1 (hash declarado) |

Nenhum teste removido, desabilitado ou renomeado. Nenhum arquivo de `src/application/`, `src/ports/` ou `src/core/` foi tocado.

**Contrastes** (WCAG, luminância relativa) medidos e anotados na folha: o pior par novo é **5,56:1** (claro) e o melhor 15,40:1; no escuro, o pior é 6,03:1. Todos acima do mínimo AA de 4,5:1.

## 4. Desvios declarados

1. **O seletor de arquivo nativo foi mantido.** O mockup desenha uma área de arrastar com botão estilizado; a entrega manteve o `<input type="file">` nativo dentro do bloco, com o nome do arquivo ao lado. Motivo: o controle estilizado exigiria esconder o input e recriar foco/teclado, e três testes dependem do `type="file"` com `accept`.
2. **A fase 3 sem árvore continua listando os relatórios já armazenados**, abaixo do estado vazio. Um teste herdado (`test_tabela_da_tela`) conta "uma tabela por aba" e falharia se a lista sumisse.
3. **O handler de ↑/↓ foi escrito** (`T020`): o componente de abas trata só as setas horizontais, e a barra é vertical. Foram 18 linhas.
4. **O literal do link ficou `escolher outra árvore`, em minúscula**, como no contrato anterior — e não `Escolher outra árvore`, como no mockup.
5. **A `<datalist>` saiu**, e os nomes passaram a viajar como JSON. Na primeira versão, `all_names` indefinida estourava o `tojson` em dois fluxos (promoção de descarte); o conserto foi `| default([], true)`.

## 5. Limites

- O **comportamento executado do combobox** (abrir, manter foco, fechar) **não** tem teste: não há navegador headless nem executor de JS no projeto. Está no checklist manual do `onboarding.md`.
- **Esse checklist não foi executado nesta sessão**, porque o ambiente do agente não tem navegador. Ele fica para o operador, junto com a conferência visual de 320 px.
- O teto de 50 opções e o filtro sem acento foram decididos por estimativa, não medidos com um GEDCOM real grande.

## 6. Arquivos

- `src/templates/index.html`
- `src/assets/app.css`
- `tests/test_tres_fases_da_tela.py` (novo, 16 testes)
- `tests/test_combobox_de_nomes.py` (novo, 9 testes)
- `tests/test_icone_de_atalho.py` (só o valor do hash e o comentário que o declara)
- `_reversa_forward/037-redesenho-das-tres-fases/` (specs, ações, evidências e estes dois rastros)
