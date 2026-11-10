# Interface: `POST /` com `action=dna_analysis` — campo novo `triangulacao_csv`

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Tipo: HTTP (formulário HTML → render de página)
> Confidência: 🟢 CONFIRMADO
> **Contrato existente alterado por acréscimo**, não por mudança: sem o campo novo, a resposta é a de hoje.

## 1. Requisição

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| `action` | texto | sim | `dna_analysis` (inalterado) |
| `gedcom_filename` | texto | sim | inalterado |
| `root_name` | texto | sim | inalterado |
| `matches_csv` | arquivo | condicional | inalterado: exigido quando não há `matches_csv_filename` |
| `matches_csv_filename` | texto | condicional | inalterado: tem precedência sobre o arquivo |
| `promover` | texto (repetido) | não | inalterado |
| **`triangulacao_csv`** | **arquivo** | **não** | **Novo.** CSV consolidado de pares; se presente, produz o bloco de grupos com desfecho |

O campo novo é **opcional** e **independente**: sem ele, o fluxo executa exatamente o caminho de antes, e o
teste de caracterização da tela continua valendo.

## 2. Resposta de sucesso

`200 OK`, HTML com os contextos de hoje **mais**:

| Contexto | Conteúdo | Quando |
|----------|----------|--------|
| `grupos` | Lista de grupos **classificados**: convergente, dividido, parcial ou sem ancestral documentado, com motivo | Somente quando `triangulacao_csv` veio |
| `triangulacao_sem_arvore` | `False` | Somente quando `triangulacao_csv` veio |

Com o campo presente, o bloco é renderizado antes dos cartões e depois do bloco de cobertura. **Nenhum outro
contexto muda** (`RF-12`): `dna_results`, `skipped_matches`, `sem_correspondencia`, `observacoes_do_arquivo`,
`cobertura`, `message` e `aviso_de_persistencia` são os mesmos de uma execução sem o arquivo.

## 3. Erros acrescentados

| Situação | Resposta | Corpo |
|----------|----------|-------|
| `triangulacao_csv` com forma de lista de matches | `200` com `success=False` | Recusa nomeando o campo correto; **a análise de DNA não é executada** |
| `triangulacao_csv` sem build declarado | `200` com `success=True` | A análise de DNA é exibida normalmente; o bloco de grupos informa que não agrupou por falta de build |

O princípio é o mesmo da leitura tolerante: **nada de silêncio**. O arquivo auxiliar não pode impedir a análise
principal de chegar à tela, e o que ele não conseguiu fazer precisa estar escrito.

Os erros de hoje (sem CSV de matches, raiz não encontrada, CSV ilegível, 404 de referência, 413 de corpo)
permanecem **idênticos** — mesma mensagem, mesmo status, mesma moldura.

## 4. Ordem de execução

1. Guarda e resolve o CSV de matches (como hoje).
2. Guarda o `triangulacao_csv`, quando presente.
3. Executa o caso de uso de DNA (como hoje) → cartões, descartes, cobertura.
4. Lê e agrupa o arquivo de triangulação; classifica contra `resultado.resultados`.
5. Renderiza: cobertura → grupos → cartões → descartes.

O passo 4 roda **depois** do núcleo e **não** pode alterar o que os passos 1–3 produziram.

## 5. Idempotência

Igual à do fluxo atual, por conteúdo dos dois arquivos. Reenviar o mesmo par de arquivos produz o mesmo HTML
(salvo o bloco novo, que é determinístico pela `RN-13`).

## 6. Limites

| Item | Valor |
|------|-------|
| Corpo | 16 MB (soma dos dois arquivos), com `413` |
| Grupos | 200, com truncamento declarado |
| Chamadas externas | nenhuma |
