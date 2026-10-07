# `T021` — medição do bloco 1 (`upload_gedcom`)

> Ponto de medição da `D-09` para o primeiro bloco extraído.
> Ver o **Desvio 2** nas "Notas de execução" do `../actions.md`: os três blocos
> foram integrados numa reescrita só do `src/app.py`, e os três arquivos de medição
> são **recortes por conjunto de casos do mesmo ponto de medição**.

## Medições

| Instrumento | Resultado | Linha de base (`T004` da feature 005) | Veredito |
|---|---|---|---|
| Suíte completa | `231 passed, 15 errors` | `178 passed, 15 errors` | ✅ nenhuma falha; os **15 mesmos** erros de ambiente |
| Paridade diferencial | `PARIDADE 100%`, exit **0** | `100%`, exit 0 | ✅ idêntico |
| Varredura de forma (`T020`) | APROVADO | — | ✅ `index()` sem passo de domínio |
| Sonda de mensagens (`T018`) | 19 casos, **0 divergências** | `mensagens_antes.json` | ✅ |

O crescimento de `178` para `231` são **53 testes novos**, todos de arquivo novo
mais três acrescentados em `tests/test_upload_seguranca.py`. Nenhum teste foi
removido, desabilitado ou reescrito para caber na mudança (`RF-16`). A conta:

| Arquivo | Testes |
|---|---:|
| `tests/test_erros_de_dominio.py` (novo) | 13 |
| `tests/test_traducao_de_erros.py` (novo) | 17 |
| `tests/test_desfecho_do_resultado.py` (novo) | 12 |
| `tests/test_porta_de_armazenamento.py` (novo) | 8 |
| `tests/test_upload_seguranca.py` (acréscimo) | 3 |
| **total** | **53** |

## Casos do bloco 1 na sonda diferencial

Os seis casos do upload, com status, classe do alerta e texto **idênticos** antes e
depois da extração:

| Caso | Medido |
|---|---|
| `upload_sem_arquivo` | `200`, `danger`, `Nenhum arquivo GEDCOM enviado.` |
| `upload_nome_vazio` | `200`, `danger`, `Nenhum arquivo selecionado.` |
| `upload_conteudo_invalido` | `200`, `danger`, `Arquivo não reconhecido como GEDCOM: não começa com a declaração 0 HEAD.` |
| `upload_conteudo_vazio` | `200`, `danger`, `Arquivo não reconhecido como GEDCOM: arquivo vazio.` |
| `upload_ok` | `200`, `success`, `Arquivo 'arvore.ged' carregado!` |
| `upload_acima_do_teto` | **`413`**, `danger`, `Arquivo maior que o limite de 16 MB.` |

Os dois casos de conteúdo recusado cobrem a decisão de §4 do `requirements.md`: a
exceção carrega **só o motivo** (`"arquivo vazio"`, `"não começa com a declaração
0 HEAD"`) e a moldura `"Arquivo não reconhecido como GEDCOM: …"` é montada pela
tabela de tradução. O texto na tela é o mesmo de antes, e é isso que prova que a
separação entre motivo e moldura não vazou para a interface.

O caso do teto é o único de todo o conjunto que **não** responde `200`, e é o único
em que a resposta vem do handler de `413` e não de um caso de uso.

## O que este bloco poderia ter quebrado, e não quebrou

- **A validação antes da gravação** (`RF-10`): o caso `upload_conteudo_invalido`
  passa pelo port, que devolve motivo sem gravar; a pasta de upload continua vazia.
  Coberto em `tests/test_porta_de_armazenamento.py` (`T027`).
- **A lista de nomes do campo de sugestão**: era derivada na rota e passou a ser
  campo do resultado tipado. Medido no servidor real (`T025`, passo 6.2): **7**
  entradas, como antes.
- **A referência devolvida ao formulário**: medida no `T025`, passo 6.2 —
  `c6926bb74ce64b88__basic.ged`, chave de conteúdo, dois underscores e nome
  original preservado.
