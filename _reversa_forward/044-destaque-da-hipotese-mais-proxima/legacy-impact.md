# Legacy impact: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Modo: **express**
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**` e
> `tests/**`. Todos os arquivos tocados estão dentro desses globs.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/relationship_hypotheses.py` | `analise-dna` | regra-nova | MEDIUM | `BANDA_DE_DESTAQUE`, `MAXIMO_DE_DESTAQUES`, `ROTULOS_DE_DESTAQUE`, `destaque_das_candidatas`; `destaque` e `distancia_da_media` no payload da candidata, e o bloco `destaque` no payload do kit |
| `src/templates/index.html` | apresentação | contrato-alterado | LOW | Caixa de destaque antes da tabela do bloco 3, marca `linha-destacada` nas escolhidas e "distância da média" em todas as linhas |
| `src/assets/app.css` | apresentação | contrato-alterado | LOW | `.destaque-da-hipotese`, `.destaque-rotulo`, `.destaque-itens`, `.destaque-ressalva`, `.linha-destacada` |
| `tests/fixtures/sample_dna.py` | — | contrato-alterado | LOW | `DNA_CSV_HIPOTESE_TRES_DESTAQUES` (154,5 cM) e `DNA_CSV_HIPOTESE_DOIS_DESTAQUES` (42,6 cM) |
| `tests/test_destaque_da_hipotese.py` | — | componente-novo | LOW | 17 casos: banda, teto, os três casos reais, a ressalva e a lista inteira |
| `tests/test_destaque_na_tela.py` | — | componente-novo | LOW | 9 casos de tela, um por quantidade e os limites |

## 2. Diff conceitual

**`core.relationship_hypotheses`.** A escolha usa a grandeza que já ordenava a lista. O que
entrou foi o **corte** (1,5× a menor distância), o **teto** (3) e o **texto** — rótulo, itens e
ressalva. Toda candidata passa a trazer `distancia_da_media` e `destaque` (falso por padrão), e
o bloco do kit passa a trazer `destaque`, que é `None` quando não há candidata.

**Template.** A caixa fica entre o cabeçalho do kit e a tabela. A tabela não muda de tamanho: a
linha destacada é a mesma linha, agora com fundo. A coluna da faixa ganha a distância, para a
ordem ser auditável linha a linha.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.3 — o cM vira **lista**, nunca um parentesco único | a lista continua com as 9 candidatas, na mesma ordem; o destaque **marca**, não substitui |
| §3.3 — a confiança é heurística do projeto | o selo `confiança:` continua vindo de `_confianca`, inalterado |
| §3.3 — nenhum número inventado | a distância é `\|média publicada − cM\|`; nada foi acrescentado à fonte |
| Aviso estático do rodapé do bloco 3 | continua igual; o destaque ganhou ressalva **própria**, além dele |
| §3.2 — o DNA não decide parentesco | nenhum veredito, caminho ou confronto foi tocado |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| Bloco 3 da tela | passa a destacar até três relações, com critério, contagem e negativa | `src/templates/index.html` |
| Payload da candidata (`possible_relationships`) | ganha `distancia_da_media` e `destaque` (aditivos) | `src/core/relationship_hypotheses.py` |
| Payload do kit (bloco de hipótese) | ganha o bloco `destaque` (aditivo) | idem |
| Heurísticas declaradas do projeto | **mais uma**: o destaque é do PROJETO, não da fonte — a fonte não ranqueia | idem, no comentário das constantes |

> **A decisão registrada:** o destaque existe porque o operador pedia um ponto de partida, e foi
> calibrado para não reintroduzir a probabilidade recusada na 043 — o texto fala em "mais próxima
> da **média publicada**", diz entre quantas relações a escolha foi feita e nega confirmação. Se
> um dia a tela voltar a dizer "mais provável", a 043 e esta feature foram desfeitas juntas.

> **Para o `/reversa-sync`:** `_reversa_sdd/domain.md#33` descreve as possibilidades; ganha o
> destaque como heurística do projeto. `_reversa_sdd/data-dictionary.md#61` (bloco por kit) ganha
> `destaque`, e `#62` (linha publicada) ganha `distancia_da_media` e `destaque`.
> `_reversa_sdd/addenda/043-…` descreve a tabela; esta emenda acrescenta a leitura de "qual delas".
