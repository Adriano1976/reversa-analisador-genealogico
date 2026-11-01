# Investigação de fundo — feature 054

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Documento de requisitos: `_reversa_forward/054-embutir-bootstrap-e-mermaid/requirements.md`

## 1. O que existe hoje

Medido no código em 2026-10-31:

| # | Onde | O que é | Origem |
|---|------|---------|--------|
| 1 | `src/templates/index.html:96` | folha do Bootstrap 5.3.3 | `cdn.jsdelivr.net` |
| 2 | `src/templates/index.html:108-110` | dois `preconnect` e a folha das duas famílias | `fonts.googleapis.com`, `fonts.gstatic.com` |
| 3 | `src/templates/index.html:128` | script do Mermaid, sem versão exata (faixa `10`) | `cdn.jsdelivr.net` |
| 4 | `src/templates/index.html:2011` | script do Bootstrap 5.3.3 (pacote consolidado com Popper) | `cdn.jsdelivr.net` |
| 5 | `src/templates/_entrada_base.html:12` | a mesma folha do Bootstrap | `cdn.jsdelivr.net` |

O `_entrada_base.html` é herdado por `login.html`, `cadastro.html`, `recuperar_senha.html`,
`redefinir_senha.html`, `definir_senha.html` e `mensagem.html`.

Sem rede, a leitura do código permite afirmar: a folha do Bootstrap não chega, então a grade, os cartões, os
botões e as tabelas perdem a base; as abas usam `data-bs-toggle="tab"` e o fechamento de alerta usa
`data-bs-dismiss="alert"`, ambos entregues pelo script do Bootstrap, que também não chega; e
`mermaid.initialize` (`index.html:2019`) referencia um global que não existe. O botão de tema é um script
próprio e continua funcionando.

## 2. Medição dos arquivos (2026-10-31)

Feita pelo Python do `.venv`, com `User-Agent` de navegador, direto nos endereços que a tela usa:

| Arquivo | Versão resolvida | Bytes | `sha256` |
|---------|------------------|------:|----------|
| `bootstrap.min.css` | 5.3.3 | 232.803 | `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8` |
| `bootstrap.bundle.min.js` | 5.3.3 | 80.721 | `0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c` |
| `mermaid.min.js` | **10.9.8** | 3.337.857 | `8d607d7ef1d077a8aa202e18e62212bfa992c68bfeabc5cf45d51a128fe6675d` |
| fontes (`woff2`) | — | 201.468 (11 arquivos) | por arquivo, na receita |

O endereço `mermaid@10` resolve hoje para **10.9.8** (`data.jsdelivr.com/v1/packages/npm/mermaid/resolved?specifier=10`).
Como o endereço não tem versão exata, a versão embutida precisa ser escolhida e fixada — e é essa a decisão
`RN-03`/`D-13`.

## 3. As fontes, e por que elas exigem receita

O CSS que o Google serve para esta tela (`css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap`)
tem **16.768 bytes**, **45 blocos `@font-face`** e aponta para apenas **11 arquivos `woff2` distintos** — porque
as duas famílias são **variáveis**: cada bloco declara uma faixa de pesos (`400 800` para Manrope, `500 700` para
Cormorant) e o mesmo arquivo cobre a faixa inteira. Cada arquivo é um **subconjunto** (`unicode-range`): latino,
latino estendido, acentos combinantes, grego e cirílico.

Três consequências práticas:

1. Não faz sentido "baixar a fonte": o que existe são 11 arquivos de subconjunto. O navegador escolhe quais baixar
   pelo `unicode-range`, exatamente como faz hoje.
2. Reescrever as URLs é a única edição necessária no CSS — os blocos, as faixas e o `font-display: swap` podem ser
   preservados literalmente.
3. O CSS tem de ser **gerado**, não escrito à mão: qualquer ajuste de peso no futuro vem de uma nova consulta ao
   Google. Por isso a receita (D-14), no molde da arte (ADR-29): receita em `tests/`, derivado commitado, teste
   que confere o derivado sem rede.

O `unicode-range` do subconjunto latino já cobre o português (`ã`, `ç`, `é`) e a pontuação tipográfica; manter os
11 arquivos evita que um nome estrangeiro num GEDCOM caia em `Georgia` glifo a glifo.

## 4. Alternativas avaliadas

| Alternativa | Por que foi descartada |
|-------------|------------------------|
| Embutir o CSS e o JS dentro do HTML | Cada resposta de `GET /` cresceria em MB; o navegador não teria cache separado por arquivo; e `SHA_DA_TELA` passaria a cobrir o conteúdo da biblioteca, tornando qualquer atualização uma mudança de tela |
| `data:` URI para as fontes dentro do CSS | Base64 acrescenta ~33 % e impede cache por arquivo; o CSS passaria de 17 KB para ~270 KB, baixado inteiro antes da primeira pintura de texto |
| `src/static/` e o diretório estático do Flask | Proibidos por `W004`/`BR-E-23` e pela `RN-07` da feature 009; há teste que falha se um recurso cair numa pasta estática |
| Uma única rota `/assets/<arquivo>` | Vira servidor estático disfarçado: o contrato deixa de ser nomeado por recurso e o prefixo nasceria público por acidente — o oposto da decisão registrada em `src/web/sessao.py` |
| *Service worker* com cache offline | Superfície nova de JavaScript, ciclo de vida próprio e nenhum ganho sobre servir os arquivos localmente |
| Manter a CDN e só documentar a degradação | É o estado atual: a tela sem estilo e sem diagrama é justamente o defeito que a feature fecha |
| Proxy da aplicação para a CDN | Mantém a dependência de rede e acrescenta latência e um ponto de falha no caminho da tela |

## 5. Como o projeto já resolveu casos análogos

- **Folha de estilo** (feature 013): saiu do `<style>` embutido e virou `src/assets/app.css` servido por
  `GET /app.css`, com `mimetype` declarado e ETag do `send_file`. É o molde direto desta feature.
- **Artes** (features 009 e 026): `src/assets/` + rota própria + receita em `tests/` + teste de deriva. O
  `src/static/` continua proibido, e a arte mora em `src/assets/` porque o `.dockerignore` é lista de permissão.
- **Favicon** (feature 026): o ícone da aba é um `data:` URI de 128×128 porque é pequeno; a decisão não escala
  para MB, e é a razão de os arquivos grandes irem por rota.
- **Lista de endpoints públicos** (features 051 e 053): fechada, nomeando endpoints, não prefixos.
- **`SHA_DA_TELA`** (feature 009 em diante): o invariante é "a tela não mudou desde a última mudança declarada", e
  a declaração vive em `_reversa_sdd/addenda/`, nunca no comentário do teste.

## 6. Padrões aplicáveis

| Padrão | Onde se aplica |
|--------|----------------|
| Recurso servido por rota explícita com `mimetype` e `send_file` | As cinco rotas (`D-03`, `D-10`) |
| Conteúdo com hash declarado e receita reprodutível | Os três arquivos e os 11 `woff2` (`RN-07`, `D-14`) |
| Lista fechada de endpoints públicos | `PUBLICOS` (`D-11`) |
| Invalidação de cache por versão na URL | `?v=` nas tags (`D-12`) |
| Declaração de mudança de tela em adendo | `SHA_DA_TELA` (`D-15`) |

## 7. Fontes externas consultadas

- `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css` (232.803 bytes, medido)
- `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js` (80.721 bytes, medido)
- `https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js` (3.337.857 bytes, versão 10.9.8)
- `https://data.jsdelivr.com/v1/packages/npm/mermaid/resolved?specifier=10` (resolução da versão)
- `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap`
  (45 blocos, 11 `woff2`, `font-display: swap`)
- `_reversa_sdd/adrs/29-arte-derivada-com-receita-unica.md` (molde de receita)
- `_reversa_sdd/adenda/013-revisao-de-design-da-tela.md` (`D-06`, o Google Fonts como terceiro host)
- Licenças: Bootstrap é MIT; Mermaid é MIT; `Cormorant Garamond` e `Manrope` são SIL Open Font License. Os
  textos de licença acompanham os arquivos, e a procedência fica no adendo.
