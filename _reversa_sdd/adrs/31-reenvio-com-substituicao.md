# ADR-31 — Reenvio com substituição, e a foto tirada antes de guardar

- **Status:** Aceito e **vigente** — vale para o GEDCOM e para o CSV, pela mesma função
- **Data da decisão:** 2026-10-10
- **Commit(s):** `926a488` ("reenvia gedcom e csv com substituicao e melhora a tela"), `1ec89a9`, dentro do ciclo `011-escolher-arquivo-da-lista`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A chave de armazenamento é derivada do **conteúdo** (`ADR-17`), e `guardar` **não sobrescreve** o que já existe. Essa combinação tem uma consequência que só apareceu quando a tela passou a **listar** os arquivos: reenviar um arquivo com o **mesmo nome visível** e **conteúdo novo** cria uma **segunda entrada**, porque a chave mudou.

Medido na pasta do operador: **duas linhas de mesmo rótulo** na aba de DNA, com dois `Familias_Sergipanas.csv` — a tela mostrava duas versões da mesma planilha e o operador não tinha como saber qual era a vigente, nem como remover a antiga.

Havia ainda um requisito de paridade a respeitar: o literal `"Arquivo 'X' carregado!"` é **contrato congelado** e está provado por golden file. A correção não podia substituí-lo em todos os casos — só onde ele seria **falso**.

## Decisão

**No reenvio, substituir: a versão anterior sai da lista, e o desfecho passa a ser declarado em três valores.**

1. **Foto de ANTES.** `guardar_com_substituicao` chama `listar(dono)` e guarda os **nomes** — antes de chamar `guardar`. É a única forma de distinguir "já existia" de "acabou de nascer", porque `guardar` não sobrescreve.
2. **Gravar primeiro, aposentar depois.** A versão nova é gravada; em seguida, **todas** as versões anteriores de **mesmo nome visível** são aposentadas (`ADR-30`). Podem ser **várias** — o operador já tinha acúmulo de antes desta regra existir, e o reenvio limpa o acúmulo.
3. **Três desfechos, com mensagem própria:**
   - `substituido` — aposentou ≥ 1: `"Arquivo 'X' atualizado: a versão anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."`
   - `identico` — aposentou 0 **e** a referência já constava da foto: `"Arquivo 'X' já estava armazenado com o mesmo conteúdo: nada mudou."`
   - `novo` — aposentou 0 **e** a referência não constava: `"Arquivo 'NOME ORIGINAL' carregado!"` — **o literal congelado, preservado**.
4. **A mesma função serve aos dois tipos de arquivo.** O ramo de DNA passou a usar `guardar_com_substituicao` em vez de um segundo bloco parecido.
5. **O aviso de substituição do CSV é ACRESCENTADO à mensagem do resultado**, nunca a substitui: a análise é o assunto da tela, e a substituição é uma nota sobre o insumo dela.

## Evidência

- `src/application/reenvio.py` (74 linhas úteis) implementa a regra; `src/app.py` a chama nos **dois** caminhos (GEDCOM e CSV).
- A ordem de decisão está no código e é a precedência: **`substituido` vence `identico`** quando os dois poderiam ser verdadeiros. Um reenvio pode ser simultaneamente "o conteúdo já existia" e "havia versão anterior": o código decide pelo que foi **movido**.
- O literal `"Arquivo '{nome original}' carregado!"` continua no caminho comum, e é o que a paridade de tela consome.
- 🟡 **A mensagem de "novo" usa `nome_original`, e não o nome visível seguro.** Os dois divergem quando o operador envia um nome com separador de caminho. É o literal congelado, preservado de propósito.
- `tests/test_reenvio_do_arquivo.py` (174 linhas úteis) e `tests/test_reenvio_do_csv.py` (137) cobrem os desfechos.

## Justificativa

**A lista precisa dizer a verdade sobre qual versão está vigente.** Duas linhas de mesmo rótulo não são apenas feiúra: elas transferem ao operador a tarefa de descobrir qual arquivo o sistema vai usar. Como o nome visível é o que ele reconhece, é ele que tem de ser único na lista.

**Preservar o literal congelado no caminho comum é o que mantém a paridade.** A tentação era trocar a mensagem de sucesso por uma terceira, "mais clara"; isso quebraria o golden file `SCR-G01`/`SCR-002` sem necessidade, porque o caso que precisava de texto novo era o do reenvio — e esse ganhou dois desfechos próprios.

## Consequências

- 🟢 **O acúmulo de versões de mesmo nome deixou de crescer** pela aplicação. O operador que reenvia cinco vezes termina com **um** arquivo na lista e quatro em `_aposentados/`.
- 🟢 **A regra vale para o CSV, e isso fechou um caso concreto:** antes, reenviar um CSV com conteúdo novo deixava duas linhas na aba de DNA.
- 🔴 **`M-07`: o desfecho não sobrevive à requisição.** `identico`, `substituido` e `novo` existem apenas para escolher a mensagem. Depois do envio, o sistema **não sabe dizer** se aquele arquivo foi novo ou idêntico — a informação morreu com a resposta, e não há como auditar substituições.
- 🟡 **O desfecho depende de uma leitura que pode falhar em silêncio.** Se `listar` devolver uma foto incompleta, um `identico` pode ser classificado como `novo`. A foto é um retrato do instante e não tem garantia de atomicidade com a escrita — é a mesma corrida de armazenamento da dívida #3.
- 🟢 **A substituição nunca apaga:** a versão anterior continua inteira na pasta de aposentados, e a mensagem diz isso.
