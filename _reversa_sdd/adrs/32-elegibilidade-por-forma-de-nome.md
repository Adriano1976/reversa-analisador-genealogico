# ADR-32 — Elegibilidade por forma de nome, e não por alfabeto fechado

- **Status:** Aceito e **vigente** — substitui a defesa descrita no `ADR-17`
- **Data da decisão:** 2026-10-10
- **Commit(s):** `d448c40` ("valida a forma do nome e protege o parse na rota"), `305855f` ("fecha o bug do nome com acento"), `852cce7` (registra a `RN-20`)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A defesa contra escape da pasta de upload era uma **forma fechada**: `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`. Ela era elegante — como a expressão exclui `/`, `\` e `..`, um valor manipulado **não tem como** escapar —, e estava registrada como a defesa do critério 5 do `BUG-20260929-QMLY`.

O defeito é que ela era **mais estreita que o gravador**. `nome_visivel_seguro` **preserva acentos e espaços de propósito** (`RF-06`): ele só troca `/`, `\` e NUL por `_`. Ou seja, a aplicação **gravava** nomes que a própria aplicação **recusava ler**.

**Medido na pasta real do operador:** **três** arquivos com acento no nome e **um** com espaço estavam **inalcançáveis**. A consequência observada foi pior que um erro: a tela dizia que o arquivo **não existia** — `"Erro: Arquivo 'X' não existe mais."` —, quando ele estava no disco, inteiro. O registro é o `BUG-20261009-6RKP`, e a regra corrigida é a `RN-20`.

## Decisão

**Trocar o alfabeto fechado por uma exigência de FORMA DE NOME, em duas funções com perguntas distintas.**

| Função | Pergunta que responde | Critério | Quem usa |
| --- | --- | --- | --- |
| `_PREFIXO_CHAVE` / `chave_recebida_e_valida` | "tem chave?" | a forma canônica `<16 hex>__<nome>` | `resolver` — é o que **lê** |
| `referencia_de_arquivo_da_pasta` | "posso tratar como nome da pasta?" | recusa barra, barra invertida, NUL, `.`, `..` e vazio; exige que o valor seja `basename` de si mesmo | `aposentar` |

1. **A defesa continua sendo de forma, e não de lista negra.**
2. **A validação vem antes de qualquer `os.path.exists`** — a ordem é a regra.
3. **`resolver` NÃO afrouxou:** ler por referência continua exigindo a forma fechada com chave.
4. **`aposentar` usa o critério mais permissivo, e é deliberado:** os arquivos sem chave são justamente os inalcançáveis, e são os que o operador mais quer tirar da lista. Exigir a chave ali os tornaria inapagáveis.
5. **A rota ganhou proteção de parse própria:** `_arvore_do_formulario` passou a distinguir "arquivo que não existe" de "arquivo que não pôde ser lido como GEDCOM", em vez de deixar a exceção crua subir.

## Evidência

- `src/utils/validate.py` tem as **duas** funções, com os docstrings declarando a diferença de escopo.
- `utils/validate.py` também expõe `pode_ser_usado` e `motivo_de_indisponibilidade`, que a tela de entrada consome — é por elas que a listagem passou a **marcar** o item indisponível em vez de escondê-lo (`D-11`).
- A mensagem da tela distingue **dois** motivos: "sem chave" e "fora da forma". Dizer "sem chave" para o arquivo acentuado seria mentir sobre o motivo.
- `tests/test_forma_da_referencia.py` (107 linhas úteis) cobre a validação; `tests/test_upload_seguranca.py` (467) cobre o escape.
- O símbolo `_FORMATO_CHAVE` **não existe mais** no código.

## Justificativa

**Uma validação que recusa o que o próprio sistema grava é um defeito, não uma defesa.** O alfabeto fechado protegia contra um vetor real e, no mesmo movimento, quebrava um requisito também real (`RF-06`). A forma de nome protege contra o mesmo vetor — barra, barra invertida, NUL, `.` e `..` continuam recusados — sem depender de um alfabeto que o gravador não respeita.

**As duas perguntas eram uma só, e precisavam ser duas.** "A referência tem a forma canônica?" e "posso tratar isto como um nome dentro da pasta?" são perguntas diferentes, com respostas diferentes para o arquivo sem chave. Separá-las foi o que permitiu afrouxar o `aposentar` **sem** afrouxar o `resolver`.

## Consequências

- 🟢 **Os quatro arquivos inalcançáveis voltaram a ser alcançáveis**, e o `BUG-20261009-6RKP` foi fechado.
- 🟢 **A tela de entrada ganhou os dois motivos de indisponibilidade** (`state-machines.md` §8) — o item indisponível passa a **aparecer marcado**, e não desaparece.
- 🟢 **A defesa em profundidade do `aposentar` ficou com duas camadas:** a forma de nome e a conferência de que o `dirname` do caminho resolvido é exatamente a pasta de upload. A primeira já garante; a segunda não confia nela.
- 🟡 **A elegibilidade passou a ser responsabilidade de dois predicados que precisam concordar.** A tela pergunta a **mesma** função que o resolvedor justamente para que a marca nunca divirja — mas a divergência entre `pode_ser_usado` e `resolver` continua sendo um risco de manutenção, e não há teste que compare as duas.
- 🔴 **O `ADR-17` precisa ser lido com esta ressalva em vigor:** a chave por conteúdo continua correta e vigente; o que caiu foi **a forma fechada como defesa única**. Ver a revalidação no `ADR-36`.
