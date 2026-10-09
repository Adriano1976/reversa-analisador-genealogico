# Regression Watch: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Origem dos itens: secao "Modificadas" do `legacy-impact.md` desta feature

## 1. Itens de vigilancia

| ID | Origem (arquivo, secao) | Regra esperada apos a mudanca | Tipo de verificacao | Sinal de violacao |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/domain.md` §4 (linha `action=dna_analysis`) | A pre-condicao e **"CSV presente OU referencia presente"**. Nenhum dos dois presentes continua recusando com a mensagem de sempre | `presenca` | A analise recusa um pedido que traz apenas `matches_csv_filename`; ou aceita um pedido sem CSV e sem referencia |
| W002 | `_reversa_sdd/domain.md` §4 | **A referencia tem PRECEDENCIA** sobre o arquivo quando os dois vem | `presenca` | O arquivo enviado junto e usado no lugar da referencia escolhida |
| W003 | `_reversa_sdd/domain.md` §4 (estado inicial da tela) | A aplicacao **nao tem mais** o estado "envie antes de tudo": `GET /` entrega as duas abas **sem envio previo** | `ausencia` | `GET /` voltar a exigir um upload antes de mostrar qualquer coisa |
| W004 | `_reversa_sdd/upload-gedcom/contracts.md#2.1` | A forma fechada do nome continua sendo a defesa contra escape, e **sem lista negra**. A `011` a reusa, nao a reimplementa | `redacao` | Aparecer um segundo padrao de nome no codigo; ou um nome com separador de caminho passar a resolver |
| W005 | `_reversa_sdd/domain.md:192` | `"Por favor, carregue o arquivo CSV de matches."` continua **literal** | `redacao` | O texto mudar sem decisao registrada |
| W006 | `_reversa_sdd/screens/golden/` | O golden `SCR-001` continua capturando o **oraculo legado congelado**, com sha256 `ec07f71b4084269a` | `presenca` | O sha256 mudar; ou alguem recapturar o golden a partir da aplicacao atual |
| W007 | `_reversa_sdd/parity/harness.py` | O harness continua **insensivel ao template**: le chaves nomeadas do contexto, e nao compara HTML | `presenca` | A paridade cair de 100 % depois de uma mudanca de tela |
| W008 | `_reversa_sdd/architecture.md` §7 (divida 8) | A aplicacao continua **sem estado entre requisicoes**: a escolha viaja por campo de formulario e nada sobrevive ao fechamento da pagina | `ausencia` | Aparecer sessao, cookie ou cache guardando a escolha do operador |

## 2. Observacoes (sem peso de regressao)

Regras que nao eram 🟢 na extracao, ou que sao consequencia de decisao desta feature e nao de regra
do legado. **Nao entram em priorizacao automatica.**

| ID | Observacao |
|----|------------|
| OBS-01 | **Duas acoes foram verificadas sem teste de tela:** `T020` (a marca de indisponivel no item) e `T021` (o campo de escolha do CSV). A `T005` prende o **calculo** de `disponivel`/`motivo`, e a `T009` prende o contrato da **rota**; o desenho no template nao tem teste que o meça |
| OBS-02 | **Conflito com a feature 009, RESOLVIDO em 2026-10-09.** `test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte` prendia o `GET /` por SHA fixo. A constante foi **atualizada** (`4b7f0b0c…` → `e18d1749…`, de 23.906 para 25.825 bytes) e o comentario dela passou a registrar quem mudou a tela e por que. Nao foi afrouxamento: o proprio comentario anterior declarava o criterio — "qualquer mudanca aqui e mudanca de tela, e nao desta feature" —, e foi o que aconteceu. O teste continua prendendo que nenhuma mudanca de tela passe despercebida. Suite final: **381 passed, 9 skipped, zero falhas** |
| OBS-03 | **`RN-11` e `RF-09` nasceram de medicao, nao de requisito original.** A auditoria da feature mediu que **7 dos 19 arquivos** sao inalcancaveis por referencia, e o plano passou a marcar o item em vez de esconde-lo |
| OBS-04 | **O defeito de raiz do nome ficou fora do escopo**, como `BUG-20261009-6RKP`: o gravador preserva acento e espaco, o resolvedor os recusa. A `011` mitiga na tela e nao conserta o contrato |
| OBS-05 | **A mitigacao de 2026-10-09 renomeou 4 arquivos da pasta real**, tirando acento e espaco do nome visivel e preservando a chave. E `temporary: true`: se o bug de raiz for corrigido para aceitar acento, as renomeacoes ficam desnecessarias |

## 3. Historico de re-extracoes

*(vazio: sera preenchido pelo agente reverso quando `/reversa` rodar de novo)*

## 4. Arquivadas

*(vazio)*
