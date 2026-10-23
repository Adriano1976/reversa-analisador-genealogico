# Plano de Transformação: OPP-20261023-DISP

- **ID**: OPP-20261023-DISP (#39)
- **Especialista**: restructure
- **Alvo**: `src/app.py` (função `index()`, linhas 561-794 na linha de base HEAD 221b6c1)
- **Objetivo**: Substituir cascata procedural de 5 ações por padrão Action Dispatcher com handlers dedicados.

## Diagnóstico

A função `index()` acumula mais de 230 linhas contendo 5 blocos acoplados:
- `upload_gedcom`
- `aposentar_arquivo`
- `selecionar_arvore`
- `dna_analysis`
- `path_search`

Cada ramo lida com parsing de requests específicos, validações locais, chamadas de casos de uso e montagem de templates, gerando alto acoplamento e baixa coesão.

## Estratégia de Refatoração

1. **Extração de Handlers Dedicados**:
   - `_acao_upload_gedcom()`: validação de arquivo, invocação do caso de uso de upload e tratamento de erros com log.
   - `_acao_aposentar_arquivo()`: invocação do armazenamento e emissão de mensagens informativas.
   - `_acao_selecionar_arvore(gedcom_filename, all_names)`: renderização do estado com árvore ativa.
   - `_acao_dna_analysis(gedcom_filename, arvore, all_names)`: extração de parâmetros do formulário (root_name, csv, promoções), invocação do caso de uso de DNA e tratamento com log.
   - `_acao_path_search(gedcom_filename, arvore, all_names)`: leitura de person1/person2, busca de parentesco e tratamento com log.

2. **Despachador Central em `index()`**:
   - `index()` passa a atuar apenas como roteador de comandos, mantendo a regra de precedência (ações pré-árvore executam antes da resolução de `_arvore_do_formulario()`).
   - Redução da função `index()` para menos de 30 linhas legíveis.

## Rede de Segurança

A suíte cobre todas as 5 ações em profundidade através de testes de integração e rotas.

## Execução (2026-10-23)

Transformação aplicada. `index()` ficou com 19 linhas e as cinco ações viraram
handlers dedicados. A suíte real foi medida nas duas pontas do lote, nesta
sessão de conciliação: 1615 passed, 9 skipped na linha de base HEAD 221b6c1 e
1615 passed, 9 skipped depois. O número de 101,58 s que este plano trazia veio
dos arquivos de evidência herdados, que não eram deste ambiente (declaravam
Python 3.12.3 e `pyproject.toml`, inexistente no projeto); foi substituído pela
medição real. O diff aplicado está em `CHG-001-despachador-de-acoes.diff`, e o
esboço anterior, que não aplicava, foi removido.
