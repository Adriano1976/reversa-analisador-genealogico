# Procedência dos arquivos embutidos — feature 054

> Medido e baixado em `2026-10-31`. Complementa `data-delta.md` e alimenta o adendo do `/reversa-sync`.

## Bibliotecas

| Arquivo | Versão | Origem | Bytes | `sha256` | Licença |
|---------|--------|--------|------:|----------|---------|
| `src/assets/bootstrap.min.css` | 5.3.3 | `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css` | 232.803 | `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8` | MIT |
| `src/assets/bootstrap.bundle.min.js` | 5.3.3 | `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js` | 80.721 | `0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c` | MIT |
| `src/assets/mermaid.min.js` | 10.9.8 | `https://cdn.jsdelivr.net/npm/mermaid@10.9.8/dist/mermaid.min.js` | 3.337.857 | `8d607d7ef1d077a8aa202e18e62212bfa992c68bfeabc5cf45d51a128fe6675d` | MIT |

Os três hashes foram conferidos contra a medição feita antes do download, e o download falharia se
divergissem. O endereço que a tela usava (`mermaid@10`) resolve hoje para **10.9.8** — a versão ficou fixa
(`D-13`).

## Fontes

Folha derivada: `src/assets/fontes.css`, **15.564 bytes**, **45 blocos `@font-face`**, **11 URLs locais**,
puro ASCII. Origem: `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap`,
consultada com `User-Agent` de navegador.

As duas famílias são **variáveis** (um arquivo cobre a faixa de pesos) e cada arquivo é um **subconjunto**
(`unicode-range`). Licença: SIL Open Font License.

| Arquivo (`src/assets/fontes/`) | Bytes | `sha256` |
|--------------------------------|------:|----------|
| `co3bmX5slCNuHLi8bLeY9MK7whWMhyjYp3tKgS4.woff2` | 33.736 | `cfa9a397d86f66c5c51775a2500a712d5f632a04f0c5eca6930dfaf612d4566d` |
| `co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpHtKgS4.woff2` | 23.416 | `a4d7cf345b8091e1d2c8c5c8fa3bd0f9bb9d00bc8988185471db398ddb5ae4c4` |
| `co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpntKgS4.woff2` | 11.220 | `6252e819a7665ae512c2d046308a9016ada63c06d0d8f96984c4b29f6c9e1bd2` |
| `co3bmX5slCNuHLi8bLeY9MK7whWMhyjYqXtK.woff2` | 37.640 | `d80df8ff5aecd299a61549f9e29ab1ed0b9b05f4ea71d50fe978e07d5240b235` |
| `co3bmX5slCNuHLi8bLeY9MK7whWMhyjYrXtKgS4.woff2` | 21.168 | `017fab69b4be8ffc08ca312823327989ade6dc3d948f0afa125e12ec2e5e7ca1` |
| `xn7gYHE41ni1AdIRggOxSuXd.woff2` | 14.352 | `447c49583b1b735cc6f566151db1d24354cec41076c55dd98455cfbde9e806c1` |
| `xn7gYHE41ni1AdIRggSxSuXd.woff2` | 9.268 | `e507c109c31789b33994646b457ee288639324516357250607c9b1398186e069` |
| `xn7gYHE41ni1AdIRggexSg.woff2` | 24.532 | `8c2def024c1bf31aacf3624ae3c4d701269b4ec3dc765c04830839f0d36b2d9e` |
| `xn7gYHE41ni1AdIRggixSuXd.woff2` | 8.388 | `dbf64d973b3987844df30992c93f47d24ac8935ee8c9b1e320942aeb1b367703` |
| `xn7gYHE41ni1AdIRggmxSuXd.woff2` | 15.160 | `2f7335119075b2079f1d882530bbc18728461612bf90743203d73a74a48f4d9b` |
| `xn7gYHE41ni1AdIRggqxSuXd.woff2` | 2.588 | `3c09135e88bbfcd848e99be137710afbb615a8d9a73c5c48e6cb0245a162af1d` |

Total das fontes: **201.468 bytes**.

## Total

`232.803 + 80.721 + 3.337.857 + 15.564 + 201.468 = 3.868.413 bytes` (~3,69 MiB) — abaixo do teto de 4 MB do
`requirements.md`.

## Como regenerar

- Bibliotecas: baixar dos endereços acima e conferir o `sha256` (o teste `tests/test_recursos_embutidos.py`
  prende os três valores).
- Fontes: `.\\.venv\\Scripts\\python.exe -m tests.fontes_da_tela` (receita com rede; o derivado é commitado e o
  teste `tests/test_fontes_da_tela.py` confere sem rede).
