# Roadmap: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Requirements: `_reversa_forward/032-arvore-sugerida-na-tela/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Três peças pequenas, nenhuma dependência nova. O núcleo ganha uma função **pura e O(1)** que deriva
o hiato e os rótulos das gerações sem tocar no grafo; o emissor Mermaid ganha uma função que
desenha o caminho corrigido a partir dos metadados; e o cartão ganha um `details` colapsável logo
abaixo do diagrama documentado, com o resumo no título.

A decisão que sustenta tudo: **a tela não chama `arvore_sugerida`**. Aquela função copia o grafo
(O(V+E)) e a análise real tem 142 cartões — numa árvore de 35.460 pessoas isso é inviável. A tela
deriva o mesmo número da mesma fórmula, e o desenho sai do caminho que ela já tem.

O JavaScript **não muda**: o handler existente pendura o `toggle` em **qualquer** `details` que
contenha `.mermaid` (`index.html:1253-1263`), e o desenho inicial ignora `details` fechado
(`:1244`). O bloco novo entra fechado e é renderizado quando o operador abre.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca entram no versionamento | Fixture sintética nos testes de núcleo e de tela | respeita |
| II. Comportamento observável preservado | O diagrama documentado, os quatro estados e o selo da `031` ficam intactos; o bloco é novo | respeita |
| III. Nenhuma mudança sem teste | Núcleo, emissor e tela têm teste; o caso negativo também | respeita |
| IV. Arestas tipadas | Só filiação é desenhada como linhagem; a rompida vai marcada | respeita |
| V. Fonte citada | O número sai da fórmula da `029`, já citada lá; a paleta vem da `030` | respeita |

Nenhum conflito com princípio ativo.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | `resumo_da_sugestao(resultado, documental)` em `core/cirurgia_do_grafo`: pura, O(1), sem grafo | A fórmula do hiato tem de ter **uma** casa; ela já mora lá (RN-07 da `029`), e a tela só precisa do número | (a) duplicar a fórmula em `reporting`; (b) chamar `arvore_sugerida` por cartão | 🟢 |
| D-02 | `mermaid_da_sugestao(...)` em `reporting/mermaid_render.py`, reusando `_mermaid_sid` e `_mermaid_label` | Um emissor por dialeto: o contrato de escape já existe ali e é o mesmo problema | (a) módulo novo só para isso; (b) Graphviz no servidor | 🟢 |
| D-03 | Quatro chaves novas no dicionário do resultado: `sugestao_geracoes`, `sugestao_resumo`, `sugestao_mermaid`, `sugestao_aviso` | O template consome os dicionários; foi o caminho da `031`, e o precedente é `confrontacao_rotulo` | (a) dataclass nova; (b) calcular no Jinja | 🟢 |
| D-04 | `<details class="arvore-sugerida">` logo **após** `details.grafo-do-registro`, fechado por padrão, com o resumo no `<summary>` | Mesma vizinhança e mesma mecânica; o JS já cobre qualquer `details` com `.mermaid` | (a) abrir por padrão; (b) seção no fim do cartão | 🟢 |
| D-05 | Cores por `classDef` e a aresta rompida por `-.->|label|` + `linkStyle` com índice | É o que o Mermaid 10 oferece sem plugin; a aresta rompida é emitida **por último** para o índice ser estável | (a) `style` inline por nó; (b) SVG gerado à mão | 🟢 |
| D-06 | Nada de cópia de grafo, nada de segundo parse; o emissor é O(nós do caminho) e só roda em cartão em conflito | 142 cartões × O(V+E) inviabilizaria; o caminho tem dezenas de nós | (a) reaproveitar `arvore_sugerida`; (b) cache de grafo | 🟢 |
| D-07 | Sem dependência, sem rota, sem tabela, sem mudança no Docker | O desenho é do navegador; o container continua sem `dot` | (a) subir o Graphviz no servidor; (b) PNG sob demanda | 🟢 |
| D-08 | O `SHA_DA_TELA` **não** muda, e isso é verificado, não suposto | A lição da `031`: o hash prende `GET /` sem resultados. Verificar antes de afirmar | (a) atualizar o hash por precaução; (b) confiar na memória | 🟢 |
| D-09 | Três arquivos de teste: núcleo (derivação), emissor (Mermaid e escape), tela (presença, ordem e ausência) | Separa o que é número, o que é texto e o que é HTML | (a) um arquivo só; (b) só teste de tela | 🟢 |
| D-10 | A frase de ausência é renderizada pelo `sugestao_aviso`, e só quando o cartão está em conflito | Quem decide é o núcleo (D-03); o template não decide regra | (a) `{% if %}` com a regra de conflito no Jinja | 🟢 |
| D-11 | O emissor Mermaid entra por **injeção** em `Dependencias`, e `src/app.py` passa a fornecê-lo | `core/` não pode importar `reporting/` — é o ciclo que o `ADR-34` fechou. O seam de injeção já existe para `generate_mermaid`, e o emissor é a mesma classe de dependência | (a) `core` importar `reporting` (recria o ciclo); (b) `application` importar `reporting` (inverte a camada); (c) montar o Mermaid no Jinja | 🟢 |

## 4. Premissas

Nenhuma premissa pendente: o `requirements.md` está com **zero** marcadores de dúvida após a sessão
de esclarecimentos de 2026-10-19 (§9).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.cirurgia_do_grafo` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-novo | Ganha `resumo_da_sugestao`, que deriva hiato e rótulos sem o grafo |
| `core.dna_analysis` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | regra-nova | Grava as quatro chaves de sugestão no dicionário do resultado |
| `reporting.mermaid_render` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-novo | Ganha `mermaid_da_sugestao`, com `classDef` e a aresta rompida |
| `tela: cartão de DNA` | `_reversa_sdd/domain.md#5-contrato-de-mensagens-ao-usuário` | contrato-alterado | Bloco colapsável da árvore sugerida, abaixo do diagrama documentado |
| `src/app.py` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | Passa `mermaid_da_sugestao` na montagem de `Dependencias` (D-11); nenhuma regra nova na borda |
| `tests.test_resumo_da_sugestao` | `tests/` | artefato-novo | Derivação do hiato nos três casos |
| `tests.test_mermaid_da_sugestao` | `tests/` | artefato-novo | Desenho, cores, aresta rompida e escape |
| `tests.test_arvore_sugerida_na_tela` | `tests/` | artefato-novo | Presença, ordem, resumo, ausência e caso negativo |

**Arquivos que NÃO mudam:** `src/assets/app.css` (as cores vão no `classDef`, não na folha),
`requirements.txt`, `init.sql`, `docker/*`, o JavaScript do template e o banco.

## 6. Delta no modelo de dados

- **Nenhuma estrutura persistente nova.** As quatro chaves vivem no dicionário em memória que a tela
  consome; o banco não recebe coluna nem linha.
- Nenhum campo novo em `sugestao`: o núcleo só lê o que a `029` e a `028` já entregam.
- Detalhe em `_reversa_forward/032-arvore-sugerida-na-tela/data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `GET /` (HTML do cartão) | HTML | `_reversa_forward/032-arvore-sugerida-na-tela/data-delta.md#4-contrato-de-tela` |

Sem contrato de rede novo e sem rota nova.

## 8. Plano de migração

n/a. Não há dado a migrar e nenhum invariante a atualizar.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Fórmula do hiato duplicada e divergente | **alto** | baixa | D-01: uma casa só; teste que compara o resumo com `arvore_sugerida` no mesmo caso |
| Custo de 142 cópias de grafo | **alto** | baixa | D-06: o núcleo não copia grafo; teste com espião que falha se `grafo.copy` for chamado |
| Sintaxe Mermaid errada (`classDef`, `linkStyle`, aresta rotulada) | médio | média | Teste de texto sobre o contrato exato; o desenho é conferido no navegador uma vez |
| Índice do `linkStyle` mudar de ordem | médio | média | A aresta rompida é emitida por último; teste que fixa o índice |
| Bloco poluir o cartão | baixo | média | Fechado por padrão, resumo curto no título |
| Frase de ausência aparecer em cartão sem conflito | médio | baixa | O `sugestao_aviso` só vem preenchido em conflito; teste do caso negativo |
| Supor que o hash muda (erro da `031`) | baixo | baixa | D-08: verificar com o cliente de teste antes de afirmar |
| Nome com aspas quebrar o Mermaid | médio | média | Reuso de `_mermaid_label`; teste com nome hostil |
| O emissor ser chamado sem estar injetado | médio | média | D-11: dependência **opcional** com padrão `None`; sem ela o cartão mostra o resumo e não o desenho, e um teste cobre esse caminho |

## 10. Critério de pronto

- [ ] `resumo_da_sugestao` no núcleo, pura e sem cópia de grafo
- [ ] `mermaid_da_sugestao` no emissor, com `classDef` e a aresta rompida
- [ ] Quatro chaves no dicionário do resultado, com `aviso` só em conflito
- [ ] Bloco colapsável abaixo do diagrama documentado, com o resumo no título
- [ ] Caso negativo: cartão sem conflito não mostra nada
- [ ] Testes de núcleo, emissor e tela passando; suíte completa verde
- [ ] `app.py`, CSS, `requirements.txt`, Docker, o JS e o banco intocados
- [ ] `git status` lista apenas os arquivos de §5 e os artefatos de `_reversa_forward/032-*`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-19 | Versão inicial gerada por `/reversa-plan` | reversa |
