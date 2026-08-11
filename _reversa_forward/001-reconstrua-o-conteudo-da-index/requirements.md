# Requirements: reconstrua o conteudo da index.html

> Identificador: `001-reconstrua-o-conteudo-da-index`
> Data: `2026-08-11`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Esta feature visa reconstruir a interface principal (`index.html`) do analisador genealógico e de DNA, para que o usuário interaja com a ferramenta através do navegador. O problema resolvido no legado é recriar o ponto central de upload de arquivos (GEDCOM e CSV) e as abas de formulários para as funcionalidades de Busca de Caminho e Analisador de DNA.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#2. Diagrama C4 — Contexto` | Aplicação monolítica, utiliza Bootstrap 5 e Mermaid.js via CDN no front-end. | 🟢 |
| `_reversa_sdd/domain.md#3. Regras de decisão e fluxo` | O front-end expõe upload de GEDCOM, e após carregado exibe abas para "Path Search" ou "DNA Analysis". | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Genealogista Genético | Acessar e utilizar as funções da aplicação via navegador web. | O usuário acessa o index, carrega o arquivo GEDCOM e em seguida interage com as abas de análise de DNA e Caminho. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O layout inicial deve solicitar apenas o upload de um arquivo GEDCOM. 🟢
   - Origem no legado: Comportamento do Jinja2 verificado na index.html.
   - Tipo: alterada/mantida (reconstrução fiel).
2. **RN-02:** Quando um GEDCOM estiver carregado, a página exibirá navegação em abas para "Buscar Conexão no GEDCOM" (Path Search) e "Analisador de DNA". 🟢
   - Origem no legado: Abas do Bootstrap na index.html.
   - Tipo: nova/mantida.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Reconstruir estrutura base do HTML | Must | A página utiliza Bootstrap 5 e possui estrutura responsiva com o container principal. | 🟢 |
| RF-02 | Estado sem GEDCOM | Must | Se nenhum GEDCOM está carregado, deve exibir um form de upload de GEDCOM. | 🟢 |
| RF-03 | Estado com GEDCOM | Must | Se um GEDCOM está carregado, exibe formulários divididos em abas para busca e análise. | 🟢 |
| RF-04 | Feedback de loading | Should | Exibir um spinner visual após submissão de formulários para indicar carregamento. | 🟢 |
| RF-05 | Exibição de resultados e gráficos | Must | Exibir os resultados dinamicamente através de Mermaid (gráficos C4) e tabelas de rejeitados. | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Utilizar CDNs | O legado já carrega Bootstrap e Mermaid via CDN. | 🟢 |
| Usabilidade | Compatibilidade e Responsividade | Uso do Bootstrap 5 (`.container`, `.row`, etc.) garante uso em diversos tamanhos de tela. | 🟢 |
| UX | Acessibilidade visual | Gráficos devem ter espaço suficiente (uso da div `.graph-container` com overflow). | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Visualização inicial sem arquivo GEDCOM
  Dado que o usuário acessa a página inicial pela primeira vez
  Quando a página carrega
  Então deve ser exibido um formulário apenas para carregar o arquivo GEDCOM

Cenário: Visualização após carregar GEDCOM
  Dado que o arquivo GEDCOM foi processado
  Quando a página recarrega
  Então a interface deve ocultar o form do GEDCOM e exibir abas para "Busca de Conexão" e "Analisador de DNA"
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Necessário como base visual de toda a aplicação. |
| RF-02 | Must | O GEDCOM é a fonte de dados primária do sistema. |
| RF-03 | Must | Permite interagir com as features fundamentais do domínio. |
| RF-05 | Must | O sistema não tem sentido se não exibir os resultados visuais (Mermaid). |
| RF-04 | Should | Opcional, porém altamente recomendado para experiência do usuário. |

## 9. Esclarecimentos

### Sessão 2026-08-11
- **Q:** Sobre a tecnologia de front-end: Devemos aproveitar para modernizar a interface utilizando frameworks client-side ou devemos manter a base atual?
  **R:** Manter estritamente Jinja2 + Bootstrap (reconstrução fiel ao legado).
- **Q:** O arquivo Mermaid é inicializado com `securityLevel: 'loose'`. Há interesse em revisar configurações de segurança para renderização do diagrama?
  **R:** Mudar para o padrão `strict` (maior segurança).

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-requirements` | reversa |
