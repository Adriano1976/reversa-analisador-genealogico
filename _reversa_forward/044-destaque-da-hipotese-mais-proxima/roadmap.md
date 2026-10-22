# Roadmap: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Modo: express

## 1. Resumo da abordagem

A grandeza que decide o destaque **já existe e já ordena a lista**: `|média publicada − cM|`.
O que faltava era um corte declarado e um texto que impedisse o corte de ser lido como
veredito. Entram duas constantes — `BANDA_DE_DESTAQUE = 1,5` e `MAXIMO_DE_DESTAQUES = 3` —,
uma função que escolhe e marca (`destaque_das_candidatas`) e um bloco `destaque` no payload,
com rótulo, itens (nome, distância, média, onde procurar) e ressalva.

A lista não muda: as N candidatas continuam no payload, na mesma ordem, e a destacada é uma
delas, agora com `destaque: True`. A tabela ganha a distância em cada linha, para a ordem ser
auditável fora da caixa.

O número 3 não é redondo por acaso: medido nos 456 kits do arquivo real, é o teto que a banda
de 1,5× alcança **uma única vez** — e com 1,25× o desenho ficaria quase sempre com um só, o que
transformaria empate real em escolha arbitrária.

## 5. Delta arquitetural

| Componente | Tipo | Arquivo alvo |
|---|---|---|
| `core.relationship_hypotheses` | regra-nova | `src/core/relationship_hypotheses.py` (`BANDA_DE_DESTAQUE`, `MAXIMO_DE_DESTAQUES`, `ROTULOS_DE_DESTAQUE`, `destaque_das_candidatas`, `destaque`/`distancia_da_media` no payload) |
| `templates/index.html` | contrato-alterado | `src/templates/index.html` (caixa de destaque antes da tabela; marca na linha; distância na coluna da faixa) |
| `assets/app.css` | contrato-alterado | `src/assets/app.css` (`.destaque-da-hipotese`, `.linha-destacada`) |
| `tests/fixtures/sample_dna.py` | contrato-alterado | `DNA_CSV_HIPOTESE_TRES_DESTAQUES`, `DNA_CSV_HIPOTESE_DOIS_DESTAQUES` |
| `tests` | componente-novo | `tests/test_destaque_da_hipotese.py`, `tests/test_destaque_na_tela.py` |
