# `T025` — verificação manual de ponta a ponta pelo `onboarding.md` §6

> 2026-10-07. Servidor de produção real (`waitress`, `python src/app.py`), porta
> `58041`, `curl.exe` como cliente. Saídas cruas em `_tmp_e2e/out/`.

## Resultado: os sete passos passam

| Passo | Medido | Esperado pelo doc | Veredito |
|---|---|---|---|
| 6.1 raiz | `status=200`, `Arquivo GEDCOM` e `Carregar e Analisar` presentes | idem | ✅ |
| 6.2 upload | `status=200`, chave `c6926bb74ce64b88__basic.ged`, **7** nomes na lista de sugestão | idem | ✅ |
| 6.3 DNA | `status=200`, `1 conexões encontradas. 0 descartadas.`, **sem** `Ocorreu um erro` | `200`, três cabeçalhos | ⚠️ ver §1 |
| 6.4a caminho direto | `status=200`, cartão `Conexão entre: Carlos Silva e Ana Silva` | idem | ✅ |
| 6.4b caminho por afinidade | `status=200`, `Conexão indireta encontrada (via casamento/afinidade).` e o aviso `...NÃO representa parentesco consanguíneo.` | idem | ✅ |
| 6.5 os três modos | `200` nos três; sem conexão → **`alert-success`**; pessoa não encontrada → **`alert-danger`** | idem | ✅ |
| 6.6 as duas mensagens negativas | `200`, `Nenhum arquivo GEDCOM enviado.` e `Nenhum arquivo selecionado.` | idem | ✅ |

O passo 6.5 é o que fecha o achado `A003` **no servidor de produção**, e não só no
cliente de teste: os dois casos em que a busca não devolve caminho têm o **mesmo
status HTTP** e são distinguidos apenas pelo modo de renderização — `SEM_RESULTADO`
sai como cartão verde, `ERRO_DE_ENTRADA` sai como alerta vermelho. O modo veio do
campo de desfecho, nunca do texto da mensagem.

## 1. Duas expectativas do `onboarding.md` não batem com o template — achado

As duas foram encontradas executando o documento, e nenhuma das duas é regressão
desta feature: `src/templates/index.html` **não foi tocado** por ela.

### 1.1 O cabeçalho do resultado de DNA

O `onboarding.md` §6.3 manda procurar `Resultados da Análise de DNA`. O template
renderiza:

```
<h2 class="text-center mt-5">Resultado da Análise</h2>
```

**Singular, e sem "de DNA".** Medido em `_tmp_e2e/out/dna.html`.

A expectativa do onboarding foi copiada de
`_reversa_sdd/migration/parity_tests/12-paridade-telas.feature:71`, que diz
"Entao o cabecalho e exatamente `Resultados da Análise de DNA`". **O Gherkin
congelado e o template divergem**, e essa divergência é anterior a esta feature —
a feature 006 não editou o template.

Consequência para esta rodada: nenhuma. O `RF-17` proíbe mudar literal visível, e
mudar o template para satisfazer o Gherkin seria exatamente a mudança que a
`RN-04` proíbe. O achado fica registrado em `../regression-watch.md` como item de
tipo `redação`, para uma extração futura decidir qual dos dois é a autoridade.

### 1.2 O padrão do passo 6.5b não pode casar

O doc manda procurar `Pessoa 1 'Zzz Ninguem' não encontrada` — com apóstrofo
literal. O Jinja escapa apóstrofo no HTML, e o que está na página é:

```
Pessoa 1 &#39;Zzz Ninguem&#39; não encontrada.
```

O texto está **correto**; o padrão é que era inalcançável. Este é um defeito do
documento, não do código, e foi corrigido nele.

## 2. Resíduo

A verificação rodou com `ANALISADOR_UPLOAD_FOLDER` apontado para
`evidence/_tmp_e2e/uploads`, e **não** para `src/uploads` como o passo 6 do
documento sugere. O documento já usa essa variável para escolher a pasta; só o
valor mudou. Efeito: os dois arquivos que a verificação grava
(`c6926bb74ce64b88__basic.ged` e `641b786ce546bff6__cm_boundaries.csv`) ficaram
isolados, e o passo 7 de limpeza manual deixa de ser necessário.

Medido: `src/uploads/` continua com as mesmas 32 entradas de antes da feature, e o
`git status` não mostra arquivo novo nenhum fora dos que esta feature criou de
propósito. O `_clean_residue.py` do instrumento de paridade foi executado.

O servidor foi encerrado e a porta `58041` voltou a recusar conexão — confirmado
por requisição depois do encerramento, porque um servidor de pé faria a próxima
execução falhar na guarda de exclusividade com um sintoma que não parece com a
causa.
