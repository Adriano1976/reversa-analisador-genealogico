# Upload e Parsing de GEDCOM, Tarefas de Implementação

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Pré-requisitos
- [ ] Dependências disponíveis: `Flask`, `ged4py`, `networkx`
- [ ] Pasta `uploads/` criada e gravável
- [ ] Variáveis de ambiente/configs de `UPLOAD_FOLDER` documentadas

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] T-01, Criar rota `GET /` que renderiza `index.html`
  - Origem no legado: `analisador-genealogico/app.py:558-559`
  - Critério de pronto: `GET /` retorna a página inicial com formulário de upload
  - Confiança: 🟢

- [ ] T-02, Implementar validação de presença e nome do arquivo no `POST /`
  - Origem no legado: `analisador-genealogico/app.py:563-567`
  - Critério de pronto: mensagens "Nenhum arquivo GEDCOM enviado." e "Nenhum arquivo selecionado." conforme o caso
  - Confiança: 🟢

- [ ] T-03, Salvar arquivo enviado em `UPLOAD_FOLDER` com nome original
  - Origem no legado: `analisador-genealogico/app.py:569-570`
  - Critério de pronto: arquivo presente em `uploads/` após POST válido
  - Confiança: 🟢

- [ ] T-04, Parsear INDI e FAM via `ged4py` e popular dicionários globais
  - Origem no legado: `analisador-genealogico/app.py:175-182`
  - Critério de pronto: `people` e `families` preenchidos após parse
  - Confiança: 🟢

- [ ] T-05, Construir grafo bidirecional e índice filho→família
  - Origem no legado: `analisador-genealogico/app.py:184-206`
  - Critério de pronto: grafo contém nós de pessoas e famílias com arestas corretas; `child_to_family` populado
  - Confiança: 🟢

- [ ] T-06, Retornar lista de nomes ordenada (com "Sem Nome" para ausentes)
  - Origem no legado: `analisador-genealogico/app.py:181`, `app.py:43`
  - Critério de pronto: lista em ordem alfabética e sem crash para pessoas sem nome
  - Confiança: 🟢

- [ ] T-07, Tratar exceções de parsing com mensagem amigável
  - Origem no legado: `analisador-genealogico/app.py:573-574`
  - Critério de pronto: GEDCOM malformado gera mensagem de erro na UI, sem quebrar o processo
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Happy path: upload de GEDCOM válido exibe lista de nomes
- [ ] TT-02, Erro: envio sem arquivo exibe "Nenhum arquivo GEDCOM enviado."
- [ ] TT-03, Erro: arquivo sem nome exibe "Nenhum arquivo selecionado."
- [ ] TT-04, Erro: GEDCOM malformado exibe mensagem de exceção

## Tarefas de Migração de Dados (se aplicável)

Não aplicável — sem banco de dados. 🟢

## Ordem Sugerida
1. T-01 e T-02 (contrato da rota e validações) primeiro — definem a interface.
2. T-03 a T-06 (núcleo de parsing/grafo) — dependem da rota existir.
3. T-07 (tratamento de erro) ao final.
4. Testes TT-01 a TT-04 após T-07.

## Lacunas Pendentes (🔴)
- Validar política de upload: aceitar extensões/tamanhos arbitrários é intencional?
- Colisão de nomes em `uploads/` (sobrescrita) precisa de tratamento?
- Estado global em memória: ok para uso single-user / single-worker?