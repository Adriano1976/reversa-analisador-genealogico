# Roadmap: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Requirements: `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Deslocar a raiz de código de `analisador-genealogico/` para `src/` como uma única renomeação de diretório, seguida da extração do arquivo de dependências para a raiz e da remoção de dois resíduos herdados. O ponto que define o custo da mudança é que **nenhum contrato muda**: os módulos do núcleo continuam sendo importados pelo mesmo nome, porque o que se move é a raiz de caminho, e não o pacote (RN-01). Por isso o trabalho se concentra em 11 linhas de código e configuração vivos e em 8 scripts de instrumentação, e não em lógica.

A ordem escolhida é: medir a linha de base antes de tocar em qualquer coisa, mover uma vez só, atualizar os consumidores, e só então reexecutar os dois gates — a suíte de testes e o comparador de paridade. Nenhuma linha de `app.py` precisa mudar, porque a pasta de templates e a pasta de upload são resolvidas a partir do próprio arquivo do aplicativo, e portanto acompanham o diretório.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A pasta de upload migra carregando **9 arquivos reais, 16.920.784 bytes**. A movimentação é de sistema de arquivos e a pasta é ignorada pelo versionador em qualquer profundidade, mas o risco de vazamento existe e vira mitigação explícita (§9). | respeita |
| II. Comportamento observável é preservado em refatoração | É o eixo da feature. O comparador de paridade é reexecutado depois da mudança e as mensagens de contrato do núcleo não são tocadas. | respeita |
| III. Nenhuma mudança sem teste que a cubra | O caminho de importação do aplicativo e a resolução do diretório de templates já são exercitados pela suíte existente — o teste de segurança de upload instancia o cliente da aplicação, força `root_path` e renderiza a tela. Um caminho errado quebra esse teste. Nenhum teste novo é necessário; decisão registrada em D-06. | respeita |
| IV. Arestas do grafo são tipadas | Não afetado: nenhuma travessia de grafo é tocada. | respeita |
| V. Toda suposição de genealogia genética cita a fonte | Não afetado: nenhum valor de domínio é alterado. | respeita |

**Nenhum princípio em conflito.**

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Mover a pasta com uma única operação de renomeação do versionador | Preserva o histórico por arquivo (detecção de rename) e não duplica bytes | `copiar e apagar` (perde histórico e dobra a exposição dos 16,9 MB); `recriar a árvore à mão` | 🟢 |
| D-02 | Mover a pasta de upload à parte, por movimentação de sistema de arquivos | Ela é ignorada pelo versionador, então a renomeação do versionador não a alcança; são 9 arquivos de dados reais que pertencem ao usuário | `deixar para trás` (o aplicativo passa a apontar para pasta inexistente); `copiar e apagar` (janela de perda) | 🟢 |
| D-03 | Não alterar nenhuma linha de `app.py` | A pasta de upload é ancorada no arquivo do aplicativo e o servidor web resolve templates pelo diretório do arquivo; os dois acompanham a renomeação sem ajuste | `reescrever as duas resoluções` (reintroduziria exatamente a classe de defeito do BUG-20260929-QMLY) | 🟢 |
| D-04 | Não alterar nenhuma linha de importação do núcleo | O nome do pacote não muda: o que muda é a raiz de caminho (RN-01) | `renomear o pacote junto` (fora de escopo, e invalidaria os instrumentos congelados do comparador) | 🟢 |
| D-05 | Atualizar os 8 scripts de instrumentação na mesma mudança | Sem eles o comparador de paridade não roda, e a prova de que o comportamento não mudou (princípio II) desaparece | `deixar os scripts para depois` (a feature ficaria sem gate) | 🟢 |
| D-06 | Não criar teste novo | A suíte já cobre o que um caminho errado quebraria: importação do aplicativo, `root_path` forçado e renderização da tela. Criar teste redundante inflaria a suíte e mudaria a contagem da linha de base, que é justamente o critério de RF-06 | `teste dedicado de layout` (redundante com o que já existe) | 🟢 |
| D-07 | Não reescrever as specs de `_reversa_sdd/`; publicar adendo | RN-03: registro histórico não é reescrito. Há 259 ocorrências de caminho na documentação de extração | `reescrever as specs` (contradiz RN-03 e destrói a rastreabilidade do que foi observado) | 🟢 |
| D-08 | Atualizar também a string de busca que o verificador de paridade guarda | Esse script armazena a própria linha de `sys.path` como texto a localizar; atualizar só o caminho real deixaria a verificação **silenciosamente sem efeito**, sem erro nenhum | `atualizar só o caminho` (degradação invisível de um gate) | 🟢 |
| D-09 | Corrigir a contagem de pontos de alteração de RF-03 | O critério fala em 9 pontos de inserção; a medição dá **16 inserções em 8 arquivos**, das quais 9 linhas nomeiam o diretório. O plano adota o critério de varredura de RF-02, que é o verificável, e trata a contagem de RF-03 como aproximada | `seguir a contagem literal` (levaria a achar que sobraram pontos quando não sobraram, ou o contrário) | 🟢 |
| D-10 | Fora de escopo: publicar o mini-site, corrigir o disparo do workflow de publicação e mexer no diretório de dados legado da raiz | Nenhum dos três é necessário para a feature; o primeiro é regeneração, o segundo é defeito pré-existente do fluxo de publicação, o terceiro foi decidido como intocado | `aproveitar a passagem` (mistura escopos e dificulta reverter) | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| — | — | — |

Nenhuma premissa: o `requirements.md` foi fechado com zero marcadores `[DÚVIDA]` após duas passadas de esclarecimentos.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Raiz do código (as duas camadas) | `_reversa_sdd/architecture.md#1` | regra-alterada | O diretório que abriga apresentação e núcleo passa a se chamar `src/`; o conteúdo é o mesmo |
| Camada de apresentação (`app.py`) | `_reversa_sdd/architecture.md#1` | regra-alterada | Muda de caminho, sem alteração de conteúdo |
| Núcleo (`reconstructed/`) | `_reversa_sdd/architecture.md#1` | regra-alterada | Muda de caminho, sem alteração de conteúdo |
| Diretório de upload | `_reversa_sdd/architecture.md#3.3` | regra-alterada | Passa a viver sob a nova raiz; continua ancorado no arquivo do aplicativo |
| Instrumentação de desenvolvimento | `_reversa_sdd/architecture.md#6` | contrato-alterado | 8 scripts passam a resolver o caminho novo; nenhum perde função |
| Arquivo de dependências | `_reversa_sdd/dependencies.md#1` | regra-alterada | Sobe para a raiz do repositório |
| `README.md` herdado do módulo | `_reversa_sdd/inventory.md#2` | componente-extinto | Removido; anunciava uma biblioteca abandonada (`architecture.md#5`, dívida 9) |
| `.gitignore.txt` do módulo | `_reversa_sdd/inventory.md#2` | componente-extinto | Removido; a única regra exclusiva apontava para artefato que o projeto deixou de gerar |
| `static/` | `_reversa_sdd/inventory.md#2` | componente-extinto | Diretório vazio removido |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma alteração de modelo**. Nenhuma entidade, campo, índice ou chave é criada, alterada ou removida. A única estrutura que muda é a localização física da pasta de upload, cujo contrato de chave (derivada do conteúdo) permanece idêntico.
- Detalhe completo em: `_reversa_forward/003-renomear-pasta-app-para-src/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo é afetado. A superfície HTTP continua sendo a rota única com despacho por campo de ação, as mensagens de contrato do núcleo permanecem literais, e o contrato do campo oculto que devolve o identificador do arquivo armazenado continua válido porque a chave é derivada do conteúdo e não do caminho.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| — | — | — (diretório `interfaces/` omitido por não haver contrato afetado) |

## 8. Plano de migração

1. **Liberar os caminhos novos na política de edição do legado** — `src/**` e `.vscode/**` em `allowedPaths`. Passo do usuário, bloqueante: sem ele a escrita é recusada pela política.
2. **Medir a linha de base, com saída gravada** — suíte de testes e comparador de paridade, antes de qualquer movimento. Linha de base medida em 2026-10-02: **118 passed, 15 errors** (todos os 15 são `PermissionError` de diretório temporário do ambiente, não falhas de código) e paridade de 100%.
3. **Renomear a raiz de código** em uma única operação de versionador, `analisador-genealogico/` → `src/`.
4. **Mover a pasta de upload** por movimentação de sistema de arquivos (9 arquivos, 16.920.784 bytes), conferindo contagem e soma de bytes antes e depois; descartar o cache de bytecode, que é regenerável.
5. **Extração e remoção dos resíduos** — `requirements.txt` para a raiz; remover o `README.md` herdado, o `.gitignore.txt` e o diretório vazio `static/`.
6. **Atualizar os 11 pontos de caminho em código e configuração vivos** — 9 linhas em 8 arquivos de teste (8 inserções de caminho e 1 definição da pasta do aplicativo, que também alimenta o `root_path` e o caminho do `app.py` no teste), 1 no `pyrefly.toml` e 1 na configuração do editor.
7. **Atualizar os 8 scripts de instrumentação**, incluindo a string de busca do verificador de paridade (D-08).
8. **Atualizar o `README.md` da raiz** — os caminhos, os comandos de instalação e execução, e a remoção das duas linhas da árvore que descrevem os artefatos extintos.
9. **Reexecutar os gates** — suíte, paridade e varredura por nome residual, comparando com a medição do passo 2.
10. **Publicar o adendo** em `_reversa_sdd/addenda/` e, quando couber, regenerar o mini-site. Passo de convergência documental, não de código.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Perda dos 9 arquivos de dados reais da pasta de upload (16,9 MB) | alto | baixa | Movimentação de sistema de arquivos, nunca copiar e apagar; conferir contagem e soma de bytes antes e depois (passo 4) |
| Dado real entrar no versionamento durante a movimentação | alto | baixa | A pasta de upload é ignorada em qualquer profundidade; conferir a saída do estado do versionador antes de encerrar (princípio I, RF-08) |
| Comparador de paridade silenciosamente inoperante por string de busca obsoleta | alto | média | D-08; conferir que a verificação continua encontrando o que procura, e não apenas que o script roda |
| Referência residual ao nome antigo em script de instrumentação ou configuração | médio | média | Varredura final por nome antigo no conjunto vivo, incluindo os 8 scripts (RF-02) |
| Documentação derivada desatualizada — mini-site e specs somam centenas de ocorrências de caminho | médio | alta | Adendo em vez de reescrita (D-07) e regeneração do mini-site; nenhuma edição manual de registro histórico |
| Contagem de testes divergir da linha de base | médio | baixa | D-06 explica por que a contagem não deve mudar; qualquer variação é investigada, não aceita |
| Publicação do mini-site continua sem rodar (o disparo aponta para branch diferente da atual) | baixo | alta | Explicitamente fora de escopo (D-10); registrado para não se perder |
| Diferenças históricas de bugs e refatoração ficam inaplicáveis após a renomeação | baixo | alta | Aceito por decisão (RN-03): são registro do que aconteceu, não artefato executável |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `src/app.py`, `src/reconstructed/` com os 12 arquivos, `src/templates/` e `src/uploads/` existem; o diretório com o nome antigo não existe (RF-01)
- [ ] `requirements.txt` na raiz; `README.md` herdado, `.gitignore.txt` e `static/` extintos (RF-01, RF-13)
- [ ] Varredura por `analisador-genealogico` no conjunto vivo retorna zero ocorrências (RF-02)
- [ ] `pyrefly.toml` com `search-path = ["src"]` (RF-04)
- [ ] Os 8 scripts de instrumentação executam e o comparador de paridade segue em 100% (RF-05, RF-07, RF-12)
- [ ] Suíte com o mesmo resultado da linha de base, sem teste removido ou desabilitado (RF-06)
- [ ] `python src/app.py` a partir da raiz sobe a aplicação e a tela renderiza (RF-09)
- [ ] Nenhum arquivo de dado real aparece no estado do versionamento (RF-08)
- [ ] Adendo publicado e rastreado por RF-11

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-02 | Versão inicial gerada por `/reversa-plan` | reversa |
