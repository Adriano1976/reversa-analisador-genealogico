# Onboarding: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Para quem vai **testar a feature pela primeira vez**, sem conhecer o código.

## 1. Antes de tudo

O projeto usa o `.venv` como interpretador oficial. Todos os comandos abaixo são PowerShell, a partir da raiz
do repositório.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q          # linha de base: tudo verde antes de testar
.\.venv\Scripts\python.exe src\app.py            # sobe em http://127.0.0.1:5000
```

**Não** defina `DATABASE_URL` para este roteiro: sem banco a feature funciona igual, e é o modo mais simples de
ver que ela não toca persistência.

## 2. As fixtures sintéticas

Nenhum arquivo real entra no repositório (`.reversa/principles.md#I`). A feature nasce com fixtures em
`tests/fixtures/sample_triangulation.py`, no molde de `sample_dna.py`, que reproduzem **as formas** medidas na
amostra real:

| Fixture | Formas que reproduz |
|---------|---------------------|
| `trio_fechado` | A-B, A-C e B-C sobre a mesma faixa do chr 7 — o caso que vira grupo |
| `cadeia` | A-B e A-C, sem B-C — o caso que **não** vira grupo |
| `acumulo` | 8+ kits, faixa curta, cM baixo — o caso que recebe o alerta |
| `dois_segmentos` | O mesmo par duas vezes no mesmo cromossomo, faixas distintas |
| `bom` | Arquivo com BOM e nomes com `*` |
| `sem_build` | Cabeçalho com `Start`/`End`, sem `B37` |

Para gerar os arquivos em disco a partir das fixtures:

```powershell
.\.venv\Scripts\python.exe -c "from tests.fixtures import sample_triangulation as s; s.gravar_todos('C:/temp/tri')"
```

O caminho e o nome da função são a **intenção** desta etapa; se o código entregar outra assinatura, ajuste o
comando — o que não pode mudar é o conteúdo dos casos.

## 3. Roteiro A — modo isolado (sem árvore)

1. Abra `http://127.0.0.1:5000`.
2. Vá à aba **Fase 3 — Analisador de DNA**.
3. Confirme que o formulário de triangulação aparece **mesmo sem árvore carregada**.
4. Envie `trio_fechado.csv`.
5. Espere: um bloco **"Grupos de triangulação"** aberto, com um grupo no cromossomo 7, a faixa de interseção
   em pb, o cM mínimo e máximo dos pares e os três kits com nome.
6. Confirme o que **não** deve existir: nenhum cartão de conexão, nenhum desfecho documental, e **nenhuma**
   média, mediana ou distribuição (é a `RN-14`).
7. Envie `cadeia.csv`: o bloco deve dizer que não há grupo e que os pares não fecham.

## 4. Roteiro B — com a análise completa

1. Suba uma árvore GEDCOM de fixture (`tests/fixtures/sample_gedcom.py`) na Fase 1 e selecione-a.
2. Na Fase 3, envie o CSV de matches de fixture e o `root_name` correspondente.
3. No mesmo envio, anexe `trio_fechado.csv` no campo de triangulação.
4. Espere: os cartões de sempre (idênticos aos de uma execução sem o arquivo novo) **mais** o bloco de grupos,
   agora com **desfecho** em cada grupo.
5. Compare com a execução anterior: cM, caminhos, vereditos e a lista de descartes não podem ter mudado
   (`RF-12`). O CSV de descartes deve sair idêntico.

## 5. Casos negativos que precisam falhar bem

| Ação | O que deve acontecer |
|------|----------------------|
| Enviar `trio_fechado.csv` no campo de **matches** | Recusa que **nomeia o campo correto**, sem produzir cartão |
| Enviar o CSV de matches no campo de **triangulação** | Recusa que nomeia o campo correto |
| Enviar `sem_build.csv` | Nenhum grupo; o texto diz que falta a declaração de build |
| Enviar arquivo vazio ou sem as colunas de par | Erro acionável, com as colunas encontradas |
| Enviar `acumulo.csv` | O grupo recebe o alerta de acúmulo com o critério escrito, e o desfecho não é alterado |

## 6. O que medir, e anotar

Estas são as medições que a feature deve deixar registradas em `evidence/`:

1. **Tempo do agrupamento** com o arquivo de 1.650 linhas da amostra real (offline, fora do repositório).
2. **Tempo com arquivo grande** — se houver um export de 100 mil linhas, medir; se não houver, declarar que não
   foi medido em vez de estimar.
3. **Número de grupos** encontrados na amostra real: a expectativa medida é **28 grupos maximais**, cobrindo
   **116 dos 351 kits**. Divergência grande é sinal de mudança de regra, não de melhoria.
4. **`SHA_DA_TELA`** antes e depois, com o delta em bytes (o bloco novo muda a tela por definição).

## 7. Onde olhar quando algo parecer errado

| Sintoma | Onde investigar |
|---------|-----------------|
| Grupo com 50 kits | O fechamento não está sendo aplicado; ver o teste do caso `acumulo` |
| Faixa do grupo maior que a de um par | A região está sendo união, e não interseção (`RN-02`) |
| Grupo some quando um par tem 6 cM | O piso está filtrando; ele deve **marcar**, não excluir (`RN-07`, `D-13`) |
| Membro não casa com a árvore | `*` não foi removido (`RF-17`) ou o nome é de uma palavra só (identidade a confirmar) |
| Cartão mudou de valor | `RF-12` violado: o bloco está influenciando o resultado |
| Apareceu média de cM | `RN-14` violada |

## 8. Critério de "testei e está bom"

- Os dois roteiros (A e B) produzem o que está descrito, sem exceção no log.
- Os cinco casos negativos falham com mensagem acionável.
- A execução sem o arquivo novo é indistinguível da de antes (comparar o HTML gerado).
- As medições da seção 6 estão em `evidence/`, com número, não com impressão.
