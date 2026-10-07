# `T022` — medição do bloco 2 (`path_search`)

> Ponto de medição da `D-09` para o segundo bloco. Ver o **Desvio 2** nas "Notas de
> execução" do `../actions.md`.

## Medições

| Instrumento | Resultado | Linha de base | Veredito |
|---|---|---|---|
| Suíte completa | `231 passed, 15 errors` | `178 passed, 15 errors` | ✅ nenhuma falha; os mesmos 15 erros de ambiente |
| Paridade diferencial | `PARIDADE 100%`, exit **0** | `100%`, exit 0 | ✅ idêntico |
| Sonda de mensagens | 19 casos, **0 divergências** | `mensagens_antes.json` | ✅ |
| Verificação manual (`T025`) | passos 6.4a, 6.4b e 6.5 passam | — | ✅ no servidor `waitress` real |

## Casos do bloco 2 na sonda diferencial

Este é o bloco em que a decisão `D-11` realmente morde, porque `path_search` é o
único fluxo em que o núcleo sinaliza **três** estados. Os oito casos:

| Caso | Status | Classe do alerta | Texto |
|---|---|---|---|
| `ref_ausente` | `200` | `danger` | `Erro: Arquivo GEDCOM não encontrado.` |
| `ref_inexistente` | `200` | `danger` | `Erro: Arquivo '0000…__nao_existe.ged' não existe mais.` |
| `ref_forma_invalida` | `200` | `danger` | `Erro: Arquivo '../app.py' não existe mais.` |
| `path_pessoa1_ausente` | `200` | `danger` | `Pessoa 1 'Zzz Ninguem' não encontrada.` |
| `path_pessoa2_ausente` | `200` | `danger` | `Pessoa 2 'Zzz Ninguem' não encontrada.` |
| `path_direto` | `200` | **`success`** | `Conexão direta encontrada (ancestral comum).` |
| `path_indireto` | `200` | **`success`** | `Conexão indireta encontrada (via casamento/afinidade).` |
| `path_sem_conexao` | `200` | **`success`** | `Nenhuma conexão encontrada entre 'Joao Silva' e 'Solo Ninguem'.` |

**Os dois últimos são o achado `A003`.** `path_sem_conexao` responde `200` **com
sucesso** — "não achei" não é erro —, e tem exatamente o mesmo status HTTP de
`path_pessoa1_ausente`, que é **erro de entrada**. Antes da extração, a distinção
era uma linha em `app.py`; depois, ela vem do campo de desfecho do resultado
tipado, e o texto da mensagem perdeu a autoridade semântica que tinha.

Três detalhes que a medição fixa:

- **`ref_forma_invalida` não escapa da pasta.** A referência `../app.py` é recusada
  pela validação de forma **dentro do port** e cai na mesma mensagem de referência
  inexistente — nenhum caminho de fora é lido, e o texto não denuncia qual das duas
  recusas aconteceu. É o comportamento do legado (BUG-20260929-QMLY, critério 5),
  preservado.
- **O aviso de afinidade continua em maiúsculas.** Medido no `T025`, passo 6.4b:
  `… ele NÃO representa parentesco consanguíneo.` É contrato do Princípio IV: a
  conexão por casamento nunca pode ser apresentada como consanguinidade.
- **O texto de `path_sem_conexao` cita `Solo Ninguem`**, uma pessoa sem família
  nenhuma no GEDCOM de teste. O caso anterior usava `Zeca Pereira`, que **tem**
  caminho indireto (João → Ana → Zeca) e por isso devolvia a mensagem de afinidade
  em vez da de "nenhuma conexão". A primeira versão da sonda media o caso errado, e
  a correção veio de olhar a saída em vez de confiar na expectativa.

## O que este bloco poderia ter quebrado, e não quebrou

- **O par `(payload, sucesso)` como critério de renderização**: o adaptador passou
  a ler o **desfecho** e a derivar dele o `success=` e o modo. Coberto
  ponta a ponta em `tests/test_desfecho_do_resultado.py`, que usa um texto
  arbitrário para provar que o modo não vem do texto (`T026`).
- **Os três literais de sucesso da busca**: `Conexão direta encontrada (ancestral
  comum).`, `Conexão indireta encontrada (via casamento/afinidade).` e a mensagem
  de "nenhuma conexão" continuam produzidos por `core/path_search.py`, que **não foi
  tocado** (`D-12`).
- **As dependências de diagrama**: continuam montadas na borda e injetadas. A
  varredura `T020` verifica que as cinco funções de dependência aparecem **só** na
  montagem única do pacote `Dependencias`, e nunca como chamada dentro de `index()`.
