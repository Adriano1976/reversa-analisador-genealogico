# Registro de Qualidade de Código (Reversa Refactor)

> GENERATED / MANAGED pelo time Code Quality do Reversa. Este README guarda as políticas do registro.
> As pastas de contexto e os artefatos de transformação nascem sob demanda.
> Criado em 2026-09-29.

## Políticas

- `control_mode`: gated
  - `gated` (padrão): leitura, análise, medição e prova de comportamento fluem sem aprovação. TODO passo que toca o código do projeto passa por gate com diff aprovado.
  - `supervised`: o agente pode aplicar transformações de baixo risco já provadas, avisando; alto risco continua com gate.
  - `autonomous`: aplica automaticamente o que estiver 🟢 e provado. Mesmo aqui têm gate obrigatório: remover código, alterar spec efetiva, enviar material a harness externo, operação destrutiva.
- `safety_net_policy`: require-characterization
  - `require-characterization` (padrão): transformação que altera estrutura ou lógica exige rede de segurança (testes existentes + caracterização) verde antes e depois.
  - `allow-unproven`: permite transformação sem rede, sempre rebaixada para 🔴 e marcada como sem prova mecânica no registro.

## Invariante do registro

Nenhuma transformação altera comportamento observável. O que não prova preservação, para no gate. Toda transformação aplicada é revertível pelo diff guardado.

## Estrutura

```
_reversa_refactor/
  README.md                         (este arquivo)
  <contexto>/                        (feature, módulo ou caso de uso)
    opportunities/                   (oportunidades detectadas, uma por arquivo)
    transformations/
      OPP-<data>-<sufixo>-<slug>/
        plan.html                    (relatório visual do plano, antes de tocar arquivo)
        safety-net/                  (testes de caracterização + resultado verde/vermelho)
        before-after/                (evidência: medição, prova de equivalência, prova de morte)
        CHG-NNN.diff                 (diffs aplicados, fonte de reversão)
        transformation.md            (registro conforme opportunity-schema.md)
    generated/                       (index e catalog regeneráveis, nunca editados à mão)
```

## Contextos deste projeto

| Contexto | Alvo principal | Oportunidades |
|----------|----------------|---------------|
| `analise-dna` | `analisador-genealogico/reconstructed/dna_analysis.py` | 4 |
| `busca-caminho` | `analisador-genealogico/reconstructed/path_search.py` | 3 |
| `upload-gedcom` | `analisador-genealogico/reconstructed/upload.py`, `domain.py`, `app.py` e dependências | 3 |

## Gate de edição do legado: LIBERADO em 2026-09-29

`.reversa/reversa-config.json` passou a `allowLegacyEdits: true` com
`allowedPaths: ["analisador-genealogico/**", "tests/**"]`, por edição do próprio usuário às
03:02:56. Quatro transformações foram aplicadas sob esse gate:

| Oportunidade | Verbo | Arquivo | Estado |
|--------------|-------|---------|--------|
| `OPP-20260929-TPSH` | restructure | `reconstructed/path_search.py` | aplicada |
| `OPP-20260929-AU76` | optimize | `reconstructed/dna_analysis.py` | aplicada |
| `OPP-20260929-32Q7` | prune | `reconstructed/dna_analysis.py` | aplicada, empilhada sobre a AU76 |
| `OPP-20260929-SEQO` | prune | `app.py`, `requirements.txt` | aplicada |

Nenhuma delas escreveu fora dos globs liberados. `tests/**` está liberado mas **não foi usado**:
as redes de segurança por caracterização e equivalência vivem em `_reversa_refactor/`, e promovê-las
a teste permanente da suíte continua sendo decisão do usuário.

## Rede de segurança disponível

- Suíte existente: 50 testes em `tests/` (`py -3.14 -m pytest`, 50 passed), verde antes e depois de
  cada uma das quatro transformações.
- Harness de paridade diferencial oráculo x reconstrução: `_reversa_sdd/parity/harness.py`, com
  fixtures sintéticas em `_reversa_sdd/parity/fixtures/`.
- Linha de base congelada antes da aplicação: `.pytest-tmp/baseline/` (fora do versionamento), usada
  como variante A nas provas de equivalência.
- Medição: todo `optimize` registra antes e depois. Os scripts de medição e de equivalência ficam
  junto de cada transformação, e aceitam `VARIANT_A_DIR` e `VARIANT_B_DIR` para comparar duas
  variantes arbitrárias do pacote.
