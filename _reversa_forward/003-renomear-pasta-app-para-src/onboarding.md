# Onboarding: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Pré-requisito: feature implementada (não o plano, a mudança em si)
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO

## 0. O que você está verificando

Que a raiz de código mudou de nome sem que nada do comportamento observável tenha mudado. A verificação tem três pernas: a suíte de testes continua com o mesmo resultado, o comparador de paridade continua em 100%, e a aplicação continua subindo e servindo os três fluxos pela tela. Nenhuma delas deve ser inferida — as três se medem.

**Regra que vale para todo este roteiro:** use apenas dado **sintético**, gerado a partir das fixtures de teste. Nunca selecione uma árvore real na tela (princípio I do projeto).

## 1. Pré-requisitos

- Python 3.x instalado e no caminho de execução.
- Nenhum ambiente virtual é necessário: o projeto roda no Python global.

## 2. Instalar dependências

Da raiz do repositório:

```bash
pip install -r requirements.txt
pip install pytest
```

## 3. Gerar os dados sintéticos de teste

Ainda da raiz do repositório:

```bash
python -c "import sys, os, tempfile; sys.path.insert(0, os.getcwd()); from tests.fixtures.sample_dna import DNA_GED, DNA_CSV_UTF8; d = os.path.join(tempfile.gettempdir(), 'reversa-sintetico'); os.makedirs(d, exist_ok=True); open(os.path.join(d,'arvore.ged'),'w',encoding='utf-8').write(DNA_GED); open(os.path.join(d,'matches.csv'),'w',encoding='utf-8').write(DNA_CSV_UTF8); print('arquivos em:', d)"
```

O comando imprime o diretório onde ficaram `arvore.ged` e `matches.csv`. A árvore contém cinco pessoas: Joaquim Silva, Marta Souza, Carlos Silva Souza, Ana Silva Souza e Lone Ranger. O CSV traz um único correspondente: Ana Silva Souza, com 200 cM.

## 4. Medir a suíte de testes

```bash
python -m pytest -q
```

**Resultado esperado:** `118 passed, 15 errors`.

Os 15 erros são de ambiente, não de código: são testes que usam diretório temporário e falham com erro de permissão quando o ambiente de execução restringe a pasta temporária do sistema. Eles falhavam do mesmo jeito antes da mudança. **O que importa é a comparação:** o número de aprovados tem de ser idêntico ao medido antes da mudança, e nenhum teste pode ter sido removido ou desabilitado.

Se o ambiente permitir diretório temporário, o resultado esperado é a suíte inteira aprovada — e aí a comparação é com a medição feita no mesmo ambiente.

## 5. Rodar o comparador de paridade

Este é o gate que prova que o comportamento não mudou: ele roda a mesma entrada contra a versão congelada do código legado e contra o código atual, e confronta os resultados.

```bash
python _reversa_sdd/parity/harness.py
```

É demorado (percorre todas as fixtures, com limite de tempo por medição). Para uma passada rápida, use uma única árvore:

```bash
python _reversa_sdd/parity/harness.py --gedcom caminho/para/arvore.ged --pares 8
```

**Resultado esperado:** `PARIDADE OK — zero divergencia` em cada fixture, e nenhuma linha `INCONCLUSIVO`. Se as fixtures ainda não estiverem materializadas em disco, rode antes:

```bash
python _reversa_sdd/parity/make_fixtures.py
```

Depois de rodar, limpe o resíduo que o comparador grava:

```bash
python _reversa_sdd/parity/_clean_residue.py
```

**Confira também a linha de identificação do candidato impressa no cabeçalho** — ela deve citar o caminho novo. Um caminho errado aí significa que o instrumento está comparando outra coisa.

## 6. Subir a aplicação e exercitar os três fluxos

```bash
python src/app.py
```

Abra `http://127.0.0.1:5000/` e faça, nesta ordem:

1. **Carga da árvore.** Envie `arvore.ged`. Esperado: mensagem de confirmação com o nome do arquivo e a lista com os cinco nomes.
2. **Busca de caminho.** Pessoa 1 `Carlos Silva Souza`, pessoa 2 `Ana Silva Souza`. Esperado: `Conexão direta encontrada (ancestral comum).`, o caminho textual e o diagrama.
3. **Análise de DNA.** Pessoa-raiz `Carlos Silva Souza`, arquivo de correspondências `matches.csv`. Esperado: uma conexão encontrada, a previsão de parentesco correspondente à faixa de 200 cM e nenhum descartado.

Para o valor exato esperado da previsão de parentesco, compare com o que está fixado em `tests/test_dna_analysis.py` (teste da análise completa) — o texto é contrato, e a faixa de 200 cM tem mais de uma relação provável por sobreposição de faixas.

## 7. Conferir o arranjo físico

```bash
python -c "import os; [print(p, os.path.exists(p)) for p in ['src/app.py','src/reconstructed/upload.py','src/reconstructed/validate.py','src/templates/index.html','src/uploads','requirements.txt','analisador-genealogico','README.md']]"
```

Esperado: os cinco primeiros e o `requirements.txt` e o `README.md` existem; `analisador-genealogico` **não** existe.

## 8. Varredura por referência residual

```bash
python -c "import os,re; alvo=re.compile('analisador-genealogico'); raizes=['src','tests','.vscode','_reversa_sdd/parity','_reversa_sdd/oracle']; ext=('.py','.toml','.json','.md','.html','.txt','.jsonl'); achados=[os.path.join(dp,f) for r in raizes for dp,dn,fn in os.walk(r) for f in fn if f.endswith(ext) and alvo.search(open(os.path.join(dp,f),encoding='utf-8',errors='ignore').read())]; achados += [p for p in ['pyrefly.toml'] if alvo.search(open(p,encoding='utf-8').read())]; print('ocorrencias vivas:', achados)"
```

**Esperado:** lista vazia. O conjunto varrido é o "vivo": código, testes, configuração e os 8 scripts de instrumentação — que são o lugar mais provável de sobrar referência. Registro histórico e documentação de extração não entram nesta varredura: eles são preservados por decisão, e é o adendo que os corrige.

Confira também o estado do versionamento:

```bash
git status --short
```

**Esperado:** nenhum arquivo de árvore GEDCOM ou de relatório de DNA listado, em nenhuma profundidade (princípio I). O diretório de dados legado da raiz permanece intocado e não aparece, porque é ignorado.

## 9. Teste negativo que vale a pena fazer

Se você tem acesso ao ambiente, force a falha de propósito e confirme que ela aparece: renomeie mentalmente um dos caminhos em um arquivo de teste para o nome antigo e rode a suíte. O erro tem de ser imediato e claro — falha de importação, não resultado silenciosamente diferente. Depois desfaça.

## 10. Reversão

Enquanto a mudança não estiver commitada, reverter é a operação inversa:

1. Renomeie a raiz de volta.
2. Mova a pasta de upload de volta para dentro dela.
3. Restaure os arquivos removidos e o `requirements.txt` pela posição original a partir do versionador.

Atenção: a pasta de upload **não** é restaurada pelo versionador, porque nunca foi versionada. Ela precisa ser movida à mão, e é o único passo da reversão que pode causar perda de dado se for esquecido.

## 11. Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Erro de importação do pacote do núcleo nos testes | Algum dos 16 pontos de inserção de caminho ficou apontando para o nome antigo | Refazer o passo 8 |
| Tela não encontra os templates | O aplicativo foi executado de um diretório diferente do esperado, ou a pasta de templates não acompanhou a movimentação | Confirmar o passo 7 e subir por `python src/app.py` a partir da raiz |
| Análise de DNA falha ao abrir o CSV enviado | A pasta de upload não acompanhou a movimentação, ou a movimentação foi feita copiando sem apagar | Conferir contagem e soma de bytes (passo 4 do plano de migração) |
| Comparador de paridade sem efeito, mas sem erro | A string de busca do verificador de paridade ficou obsoleta (decisão D-08 do roadmap) | Conferir se a verificação ainda encontra o que procura, e não apenas se o script roda |
| Mini-site ainda cita o caminho antigo | Regeneração não executada | É o passo de convergência documental do plano, não bloqueia o código |
