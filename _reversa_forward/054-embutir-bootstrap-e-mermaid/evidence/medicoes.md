# Medições — feature 054

> Data: `2026-10-31`, com `ANALISADOR_MODO_TESTE=1` e pasta de upload temporária.
> Cliente de teste do Flask: mede o custo da aplicação, **não** o da rede.

## Tempo por rota

| Rota | Status | Bytes | Mediana (5 execuções) |
|------|-------:|------:|----------------------:|
| `/` | 200 | 51.218 | 2,7 ms |
| `/bootstrap.css` | 200 | 232.803 | 2,5 ms |
| `/fontes.css` | 200 | 15.564 | 2,1 ms |
| `/app.css` | 200 | 89.954 | 5,0 ms |
| `/mermaid.js` | 200 | 3.337.857 | 3,5 ms |
| `/bootstrap.js` | 200 | 80.721 | 2,7 ms |
| `/fontes/<subconjunto latino>.woff2` | 200 | 33.736 | 3,0 ms |

Nenhuma rota passa de 5 ms: é leitura de disco mais `send_file`, como a folha já fazia.

## Peso da primeira carga

Soma dos recursos referenciados pela tela (HTML + cinco folhas/scripts + um subconjunto de fonte):
**3.841.853 bytes** (~3,66 MiB).

O teto declarado no `requirements.md` é de 4 MB para a soma dos arquivos embutidos; a soma dos
arquivos em `src/assets/` (três bibliotecas + folha de fontes + 11 `woff2`) é **3.868.413 bytes** —
abaixo do teto.

## O que o navegador baixa de fato

O CSS das fontes tem 45 blocos com `unicode-range`: o navegador baixa **só os subconjuntos que a
página usa**. Numa tela em português, isso costuma ser o latino (33.736 bytes de Cormorant e 24.532 de
Manrope) e, se houver acento combinante, mais um arquivo. Os dez arquivos restantes existem para nomes
estrangeiros vindos de GEDCOM, e não são transferidos sem uso.

## Rebusca

Os cinco recursos saem com `ETag` e `Last-Modified` do `send_file`, como as artes: a segunda carga é
`304` sem corpo quando o arquivo não mudou. O `?v=` nas tags é conveniência de invalidação, não
correção de cache.

## Fora do escopo desta medição

Não há medição de tempo de rede, de primeira pintura ou de renderização do Mermaid: o ambiente do
agente não tem navegador. A conferência visual está em `evidence/conferencia.md`.
