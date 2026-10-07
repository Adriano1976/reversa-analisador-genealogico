# Evidências da execução do `actions.md` — feature `007-dono-no-port-e-baseline`

> Rodada de `/reversa-coding`, 2026-10-07.
> Este diretório guarda as **medições**, não as conclusões. As conclusões ficam em
> `../legacy-impact.md` e `../regression-watch.md`; os avisos de execução ficam em
> `../actions.md` § "Notas de execução".

## 1. Os cinco instrumentos, e o que cada um responde

| Instrumento | Comando | Pergunta que responde |
|---|---|---|
| Suíte | `.venv\Scripts\python.exe -m pytest -q` | A suíte executa inteira? Algum aprovado virou falha? |
| Paridade diferencial | `.venv\Scripts\python.exe _reversa_sdd\parity\harness.py` | O núcleo continua idêntico ao oráculo congelado? |
| Sonda de mensagens | `.venv\Scripts\python.exe evidence\probe_mensagens.py depois` + `_comparar_007.py` | O **texto da tela** e o **modo de renderização** mudaram desde a entrega da 006? |
| Varredura de forma | `.venv\Scripts\python.exe evidence\_t011_varredura.py` | Todo chamador de porta passa o dono, e a constante é única? |
| Verificação manual | roteiro do `../onboarding.md` | A aplicação funciona de ponta a ponta, e não deixa resíduo? |

⚠️ **Todos os comandos usam o interpretador oficial, `.venv/Scripts/python.exe`.** É
o que a `RF-08` e a `RF-10` exigem, e o motivo está em `../investigation.md` §2.

## 2. Medições, por ação

| Arquivo | Ação | O que registra |
|---|---|---|
| `T004-suite-bloco0.txt` | `T004` | Saída crua da suíte no fim do Bloco 0 — `249 passed`, exit 0 |
| `T004-paridade-bloco0.txt` | `T004` | Saída crua da paridade no fim do Bloco 0 — `100 %`, exit 0 |
| `T004-linha-de-base-bloco0.md` | `T004` | A leitura da linha de base: aritmética, o que o Bloco 0 provou, e a asserção errada do `T003` |
| `T011-varredura.txt` | `T011` | Saída da varredura de forma — **APROVADO**, 5 chamadores, 1 constante |
| `T012-mensagens.txt` | `T012` | Comparação dos 19 casos — **idênticos**, status, classe do alerta e texto |
| `T014-suite-bloco1.txt` | `T014` | Saída crua da suíte no fim do Bloco 1 — `261 passed`, exit 0 |
| `T014-paridade-bloco1.txt` | `T014` | Saída crua da paridade no fim do Bloco 1 — `100 %`, exit 0 |
| `T015-verificacao-manual.md` | `T015` | Os três fluxos contra `waitress`, os `413`, o encerramento verificado e a ausência de resíduo |
| `T016-conferencia-de-escopo.md` | `T016` | O `diff` por arquivo, os quatro pacotes intocados, os 13 diretórios presos e o resíduo de instrumento |

## 3. Instrumentos, e por que eles ficam aqui

| Arquivo | O que é |
|---|---|
| `probe_mensagens.py` | **Cópia byte a byte** da sonda que a feature 006 entregou (hash conferido). Roda os 19 casos contra o `app.py` atual |
| `_comparar_007.py` | Compara a saída da sonda contra o baseline da 006, caso a caso. Sai 1 em divergência |
| `mensagens_baseline_006.json` | **Cópia** do `mensagens_depois.json` da entrega da 006 — o lado "antes" desta feature |
| `mensagens_depois.json` | Saída da sonda agora |
| `_t011_varredura.py` | Varredura por AST dos chamadores de porta e da constante de dono |
| `_acoes.py` | Marca `[X]` por ID no `actions.md` e anexa linhas ao `progress.jsonl` |
| `_tmp_e2e/*.html` | Saídas cruas dos `curl` da verificação manual, uma por passo |

**Por que `probe_mensagens.py` é uma cópia, e não uma chamada ao da 006:** a sonda
grava a saída **ao lado de si mesma**, com o rótulo recebido. Rodá-la de dentro da
pasta da 006 sobrescreveria `mensagens_depois.json`, que é **artefato entregue**
daquela feature. A cópia roda na pasta desta feature e não toca em nada de lá.

## 4. O que este diretório **não** contém

- **Não** contém saída de execução no interpretador global. A divergência de versões
  entre o global e o `.venv/` foi medida em 2026-10-07, na sessão de esclarecimento,
  e não alterou resultado observável — mas o instrumento oficial é o `.venv/`, e é
  ele que produziu tudo o que está aqui.
- **Não** contém o estado de `src/uploads/`. A verificação manual aponta a pasta para
  `_tmp_e2e/uploads`, e a pasta real não foi tocada (ver `T015` §2).
