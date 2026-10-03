# Requirements: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O diretório que hoje se chama `analisador-genealogico/` passa a se chamar `src/`, e todas as referências ao nome antigo em código, configuração e documentação viva passam a apontar para o novo nome. O conteúdo e o comportamento do sistema não mudam: a suíte de testes continua verde e a paridade de comportamento com o oráculo continua em 100%. A mudança é para o mantenedor do repositório, que ganha uma árvore alinhada à convenção `src/` e deixa de ter um diretório cujo nome descreve o projeto em vez do papel que ele exerce. O problema que ela resolve é de leitura do repositório: hoje a raiz do código carrega o mesmo nome do produto, o que a torna indistinguível de um pacote importável e obriga todo consumidor a saber de cor um caminho com hífen.

Neste documento, **raiz da aplicação** e **diretório do código** designam o mesmo diretório; **oráculo** designa a versão do código congelada por commit e usada como referência de comportamento; **candidato** designa o código atual, que é comparado contra ela.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/inventory.md#2` | Árvore canônica do projeto: `analisador-genealogico/` é a raiz que contém `app.py`, `requirements.txt`, `README.md`, `.gitignore.txt`, `reconstructed/`, `templates/` e `uploads/` | 🟢 |
| `_reversa_sdd/inventory.md#4` | Pontos de entrada e configuração: `analisador-genealogico/app.py`; `pyrefly.toml` com `search-path = ["analisador-genealogico"]`; `pytest.ini` com `testpaths = tests` | 🟢 |
| `_reversa_sdd/architecture.md#1` | Duas camadas com contratos opostos — apresentação (`app.py`, 84 linhas) e núcleo (`reconstructed/`, 1117 linhas) — ambas **dentro** do diretório a renomear | 🟢 |
| `_reversa_sdd/architecture.md#3.3` | A pasta `uploads/` é uma das estruturas de runtime do sistema, ao lado das globais em memória | 🟢 |
| `_reversa_sdd/architecture.md#6` | A instrumentação de desenvolvimento (oráculo congelado, harness de paridade, goldens) fica fora do runtime, mas referencia o caminho do diretório | 🟢 |
| `_reversa_sdd/code-analysis.md#1` | Mapa de dependências entre rota e núcleo, expresso inteiramente em caminhos do diretório a renomear | 🟢 |
| `_reversa_sdd/domain.md#7` (ADR-02) | Decisão registrada de promover os módulos para `analisador-genealogico/reconstructed/` e reduzir `app.py` a camada de rota fina | 🟢 |
| `_reversa_sdd/domain.md#4.1` | Mensagens do núcleo são **texto de contrato** com dependência literal por golden files | 🟢 |
| `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md#2` (vigente) | A chave de armazenamento é derivada do conteúdo e gravada sob a pasta de upload do aplicativo | 🟢 |
| `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md#5` (vigente) | A validação precede a gravação: arquivo recusado não fica em disco | 🟢 |
| `.reversa/principles.md#II` | Comportamento observável é preservado em refatoração: mesmas entradas, mesmas saídas | 🟢 |
| `.reversa/principles.md#I` | Dados reais de DNA/GEDCOM nunca entram no versionamento, em nenhum caminho | 🟢 |
| `.reversa/principles.md#III` | Nenhuma mudança sem teste que a cubra | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Mantenedor do repositório | Ter a árvore alinhada à convenção `src/`, sem um diretório nomeado como o produto | Abre o repositório e lê a estrutura de pastas |
| Contribuidor novo | Rodar a suíte e o app logo após o clone, sem descobrir caminho por tentativa | Clona, instala dependências e roda `pytest` da raiz |
| Quem lê as specs e o mini-site | Confiar que os caminhos citados na documentação existem no disco | Segue uma citação de caminho de `_reversa_sdd/` até o arquivo real |
| Quem opera o gate de paridade | Comparar oráculo e candidato e ler no log qual diretório foi avaliado | Executa o harness de paridade (comparador diferencial que roda a mesma entrada contra o oráculo congelado e contra o código atual, e confronta os resultados) e lê o caminho do candidato impresso |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O diretório que contém o código da aplicação é uma **raiz de caminho de importação**, não um pacote importável; a identidade dos módulos do núcleo (`reconstructed.*`) independe do nome desse diretório. 🟢
   - Origem no legado: `_reversa_sdd/inventory.md#4` (o `search-path` e o `sys.path` dos testes existem justamente porque o diretório é uma raiz, e não um pacote)
   - Tipo: nova — formaliza um contrato que hoje só existe implícito nos arquivos de configuração
2. **RN-02:** Nenhuma regra de negócio do núcleo é criada, alterada ou removida por esta feature. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#4.1` (as mensagens de contrato permanecem literais)
   - Tipo: n/a — declaração explícita de não-impacto, exigida pelo princípio II

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O diretório do código da aplicação passa a se chamar `src` | Must | Existe `src/app.py` e `src/reconstructed/` com os 12 arquivos do pacote; o diretório com o nome antigo não existe mais | 🟢 |
| RF-02 | Toda referência ao nome antigo em código e configuração viva é atualizada | Must | Varredura por `analisador-genealogico` em `src/`, `tests/`, `pyrefly.toml` e nos scripts executáveis de `_reversa_sdd/` retorna zero ocorrências | 🟢 |
| RF-03 | Os arquivos de teste resolvem o diretório pelo novo nome | Must | Os 9 pontos de inserção de caminho nos 8 arquivos de `tests/` apontam para `src` | 🟢 |
| RF-04 | A configuração do analisador estático aponta para o novo diretório | Must | `pyrefly.toml` contém `search-path = ["src"]` | 🟢 |
| RF-05 | Os scripts executáveis de instrumentação resolvem o novo caminho | Must | Os 8 scripts sob `_reversa_sdd/` (7 em `parity/`, 1 em `oracle/`) executam sem erro de caminho inexistente | 🟢 |
| RF-06 | A suíte de testes permanece verde e com o mesmo conjunto | Must | `pytest` da raiz do repositório mantém o resultado da linha de base, sem teste removido ou desabilitado | 🟢 |
| RF-07 | O comportamento observável do sistema é idêntico ao anterior | Must | O harness de paridade continua reportando 100%, sem divergência nova | 🟢 |
| RF-08 | A pasta de upload continua fora do versionamento e ancorada no arquivo do app | Must | `git status` não lista `src/uploads/`; escrita e leitura do upload usam o mesmo caminho, independentemente do diretório corrente | 🟢 |
| RF-09 | O `README.md` é atualizado apenas nas referências de caminho | Should | As 6 linhas de caminho citam `src/`; o nome do projeto, os créditos e as URLs externas permanecem inalterados | 🟢 |
| RF-10 | A configuração do editor é atualizada | Should | `.vscode/settings.json` referencia `./src` e não o nome antigo | 🟡 |
| RF-11 | A documentação derivada reflete a nova árvore | Should | O mini-site é regenerado e as specs recebem addendum; nenhuma citação de caminho aponta para diretório inexistente | 🟡 |
| RF-12 | O log do gate de paridade identifica o diretório correto do candidato | Should | A linha de identificação do candidato impressa pelo harness cita o novo caminho | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Consistência | Nenhuma mudança de comportamento observável: mesmos caminhos, mesmos matches aceitos e rejeitados, mesmas mensagens | `.reversa/principles.md#II`; `_reversa_sdd/domain.md#4.1` | 🟢 |
| Testabilidade | A suíte roda a partir da raiz do repositório sem alteração do `pytest.ini` | `_reversa_sdd/inventory.md#4` | 🟢 |
| Portabilidade | A resolução de caminho nos testes continua independente do diretório corrente | Os 8 arquivos de `tests/` derivam o caminho de `__file__`, e não do CWD | 🟢 |
| Rastreabilidade | Nenhum nome de módulo do núcleo muda; nenhuma linha de `import` de `reconstructed.*` é tocada | `_reversa_sdd/code-analysis.md#1` | 🟢 |
| Segurança e privacidade | Nenhum dado real de DNA/GEDCOM entra no versionamento durante a movimentação | `.reversa/principles.md#I`; `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md#2` | 🟢 |
| Governança | A escrita no destino depende de o caminho novo constar em `allowedPaths` de `.reversa/reversa-config.json`; a edição desse arquivo é ato exclusivo do usuário | `.reversa/reversa-config.json` (hoje só libera o nome antigo, `tests/**`, `README.md` e `pyrefly.toml`) | 🟢 |
| Observabilidade | Todo script que imprime o caminho avaliado passa a imprimir o caminho novo, para não mentir no log do gate | `_reversa_sdd/architecture.md#6` | 🟡 |
| Reprodutibilidade | O resultado do gate de paridade é reexecutado depois da movimentação, não presumido | `.reversa/principles.md#II` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: suíte verde depois da renomeação
  Dado que o diretório do código foi renomeado para src
  Quando o mantenedor executa a suíte de testes a partir da raiz do repositório
  Então o resultado é idêntico ao da linha de base, sem teste removido
  E os arquivos de teste resolvem o núcleo pelo novo diretório
  E nenhuma falha nova aparece por caminho não encontrado

Cenário: aplicação continua subindo e servindo a tela
  Dado que o diretório do código foi renomeado para src
  Quando o mantenedor inicia a aplicação
  Então a rota principal responde com a tela renderizada
  E os recursos de template continuam sendo encontrados

Cenário: upload continua legível na requisição seguinte
  Dado que um arquivo GEDCOM foi aceito e gravado sob a pasta de upload do novo diretório
  Quando a requisição seguinte devolve o identificador do arquivo armazenado
  Então a árvore é reencontrada e analisada
  E o arquivo está no mesmo caminho em que foi gravado, qualquer que seja o diretório corrente

Cenário: gate de paridade inalterado
  Dado que o diretório do código foi renomeado e os scripts de instrumentação foram atualizados
  Quando o mantenedor executa o harness de paridade
  Então o resultado permanece 100% de paridade, sem divergência nova
  E o log identifica o diretório do candidato pelo caminho novo

Cenário: nenhuma referência residual ao nome antigo
  Dado que a renomeação foi concluída
  Quando o mantenedor varre o código, os testes, os arquivos de configuração e os scripts executáveis pelo nome antigo
  Então nenhuma ocorrência é encontrada fora dos registros históricos
  E nenhuma citação de caminho na documentação derivada aponta para diretório inexistente

Cenário: dado real não vaza para o versionamento
  Dado que a pasta de upload mudou de lugar junto com o código
  Quando o mantenedor inspeciona o estado do versionamento
  Então nenhum arquivo de árvore GEDCOM ou de relatório de DNA aparece como rastreado ou pendente
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a própria feature; sem ela nada mais se aplica |
| RF-02 | Must | Referência residual ao nome antigo quebra o consumidor que a encontra |
| RF-03 | Must | Sem isso a suíte não importa o núcleo e o pipeline para |
| RF-04 | Must | Sem isso a verificação estática perde o núcleo inteiro |
| RF-05 | Must | Os scripts de instrumentação são o gate de comportamento da mudança |
| RF-06 | Must | Princípio III: a suíte é a prova de que nada quebrou |
| RF-07 | Must | Princípio II: refatoração não muda comportamento |
| RF-08 | Must | Princípio I e contrato do upload dependem da pasta ancorada |
| RF-09 | Should | Documentação desatualizada não quebra execução, mas engana |
| RF-10 | Should | Configuração de editor é conveniência de quem mantém |
| RF-11 | Should | Documentação derivada é regenerável; não bloqueia a mudança de código |
| RF-12 | Should | Afeta a leitura do gate, não o resultado dele |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] **Escopo do conteúdo do diretório:** `src/` recebe apenas o código (`app.py` e `reconstructed/`) ou também os itens que hoje vivem ao lado dele (`templates/`, `requirements.txt`, `uploads/`, `README.md` do módulo e `.gitignore.txt`)? A resposta muda o alocamento de recursos do servidor web, que resolve os templates a partir do diretório do arquivo de entrada, e o alocamento do diretório de upload.
- 🔴 [DÚVIDA] **Forma do diretório:** `src/` plano, apenas com o nome trocado, ou `src/` contendo um pacote com nome importável e metadados de instalação? A segunda forma elimina os pontos de inserção de caminho nos testes e a configuração de caminho do analisador estático, mas é uma mudança estrutural maior, e não apenas uma renomeação.
- 🔴 [DÚVIDA] **Resíduos e itens fora da política:** o que fazer com o diretório vazio `static/`, com o arquivo `.gitignore.txt` (cujo sufixo impede o Git de lê-lo), com o `README.md` em inglês do módulo e com o diretório `uploads/` legado da raiz — mover junto, manter onde estão ou remover? E a configuração do editor, que hoje está fora dos caminhos liberados, entra no escopo ou fica de fora?

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-02 | Versão inicial gerada por `/reversa-requirements` | reversa |

## Pendências de Qualidade

> Avaliação contra `.reversa/templates/quality-template.md` após três ciclos de revisão: 17 dos 20 itens aprovados, 3 registrados abaixo. Nenhum é CRITICAL. Veredito: **Aprovado com ressalvas**.

- **Q-013 | EdgeCases — reprovado.** Estados vazios foram considerados apenas para o diretório `static/`. O diretório de upload pode estar vazio na primeira execução, e esta feature não acrescenta cenário próprio para isso.
  > sugestão: acrescentar cenário de primeira execução com pasta de upload inexistente.
- **Q-017 | SoluçãoImplícita — reprovado.** Alguns critérios de aceite citam a contagem de pontos de alteração, o que tangencia o *como*.
  > motivo: sem a contagem, o critério de "referência residual" deixa de ser verificável de forma objetiva.
  > sugestão: manter, e tratar a contagem como métrica de verificação, não como instrução de implementação.
- **Q-018 | SoluçãoImplícita — reprovado.** O documento nomeia `pyrefly.toml` e o caminho de configuração do editor.
  > motivo: o nome do arquivo **é** o objeto da mudança e aparece no critério de aceite; não há como descrever o requisito sem citá-lo.
  > sugestão: nenhuma. Corrigir tornaria o requisito inverificável.

