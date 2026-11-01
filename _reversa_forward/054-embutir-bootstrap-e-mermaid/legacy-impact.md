# Impacto no legado — feature 054

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**` e `README.md` — todos os caminhos tocados por esta
> feature estão dentro da lista.

## 1. Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `src/assets/bootstrap.min.css` | Apresentação / inventário de recursos | `componente-novo` | MEDIUM | Folha do Bootstrap 5.3.3, byte a byte a oficial |
| `src/assets/bootstrap.bundle.min.js` | Apresentação / inventário de recursos | `componente-novo` | MEDIUM | Script do Bootstrap 5.3.3 (com Popper) |
| `src/assets/mermaid.min.js` | Apresentação / inventário de recursos | `componente-novo` | MEDIUM | Mermaid 10.9.8; versão deixou de ser a faixa `10` |
| `src/assets/fontes.css` | Apresentação / inventário de recursos | `componente-novo` | LOW | Folha derivada do Google Fonts, 45 blocos, URLs locais |
| `src/assets/fontes/*.woff2` (11) | Apresentação / inventário de recursos | `componente-novo` | LOW | Subconjuntos das duas famílias variáveis |
| `src/app.py` | Borda HTTP | `regra-nova` | MEDIUM | Cinco constantes de caminho e cinco chaves de `config` |
| `src/web/rotas_assets.py` | Blueprint `assets_bp` | `contrato-novo` | HIGH | Cinco rotas de recurso embutido; conjunto fechado de fontes |
| `src/web/sessao.py` | Guarda de sessão | `contrato-alterado` | MEDIUM | `PUBLICOS` cresce com os cinco endpoints (lista fechada) |
| `src/templates/index.html` | Apresentação — tela principal | `contrato-alterado` | HIGH | Quatro tags de CDN → quatro tags locais; `<head>` reescrito |
| `src/templates/_entrada_base.html` | Apresentação — telas de identidade | `contrato-alterado` | MEDIUM | Tag do Bootstrap passa a ser local |
| `tests/test_icone_de_atalho.py` | Invariante de tela (`SHA_DA_TELA`) | `contrato-alterado` | HIGH | Hash novo, com delta e razão declarados |
| `tests/fontes_da_tela.py` | Receita de recurso derivado | `componente-novo` | LOW | Receita da folha de fontes, com hashes |
| `tests/test_recursos_embutidos.py` | Contrato de recurso | `componente-novo` | MEDIUM | Prova das cinco rotas e dos `sha256` |
| `tests/test_recursos_degradacao.py` | Contrato de recurso | `componente-novo` | MEDIUM | 404 sem derrubar a tela; conjunto fechado |
| `tests/test_fontes_da_tela.py` | Receita de recurso derivado | `componente-novo` | LOW | Derivado conferido sem rede |
| `tests/test_tela_sem_origem_externa.py` | Contrato de tela | `componente-novo` | HIGH | Nenhum documento referencia host externo |
| `tests/test_fabrica_do_app.py` | Contrato de rotas | `contrato-alterado` | LOW | A lista fechada de rotas cresce |
| `tests/test_cabecalho_de_enquadramento.py` | Contrato de borda | `contrato-alterado` | LOW | As rotas novas entram no alcance do `X-Frame-Options` |
| `tests/test_sessao_e_guarda.py` | Contrato de sessão | `contrato-alterado` | LOW | Os recursos novos continuam públicos |
| `tests/test_host_permitido.py` | Contrato de borda | `contrato-alterado` | LOW | Os recursos novos entram no alcance da recusa de `Host` |
| `tests/verificacao_no_conteiner.py` | Empacotamento (`L-33`) | `contrato-alterado` | MEDIUM | A verificação na imagem cobre os recursos embutidos |
| `README.md` | Documentação de pilha | `regra-alterada` | LOW | "por CDN" deixa de valer para as três bibliotecas e as fontes |

## 2. Diff conceitual por componente

**Borda HTTP (`src/app.py`).** O módulo ganhou cinco constantes de caminho derivadas de `__file__` e as
publicou em `create_app`, no molde exato de `ESTILO_DA_TELA`. Nada de regra nova: é configuração de
recurso, e continua sendo o ponto que os testes usam para simular arquivo ausente.

**Blueprint `assets_bp` (`src/web/rotas_assets.py`).** É o coração da mudança. As quatro rotas antigas
não foram tocadas; entraram cinco novas: `GET /bootstrap.css`, `GET /bootstrap.js`, `GET /mermaid.js`,
`GET /fontes.css` e `GET /fontes/<arquivo>.woff2`. A última valida o nome contra um conjunto fechado de
11 nomes — o nome vem do cliente, então ele não vira caminho antes de passar pela lista. Todas declaram
`mimetype` explícito e respondem `404` vazio para ausência, no regime das artes.

**Guarda de sessão (`src/web/sessao.py`).** `PUBLICOS` é lista fechada que nomeia endpoints; os cinco
endpoints novos entraram. Sem isso, a tela de entrada — servida a quem não tem sessão — perderia a folha
e o desenho.

**Apresentação.** Em `index.html`, as quatro tags externas viraram locais (`/bootstrap.css?v=5.3.3`,
`/fontes.css?v=1`, `/mermaid.js?v=10.9.8`, `/bootstrap.js?v=5.3.3`), com a ordem preservada: Bootstrap
antes de `app.css`, Mermaid no `<head>`, Bootstrap JS no fim do corpo. Em `_entrada_base.html`, só a tag
do Bootstrap mudou; as seis telas de identidade continuam **sem** a webfont, como antes.

**Invariante de tela.** `SHA_DA_TELA` passou de `577a17fd…` (51.612 bytes) para `3487986a…` (51.218,
−394 bytes). O delta é só `<head>`: três tags externas saíram, duas locais entraram, e as duas restantes
trocaram de endereço sem mudar de posição.

## 3. Preservadas

Nenhuma regra de negócio do `_reversa_sdd/domain.md` foi alterada: a feature não toca matching, cM,
travessia de grafo, `aposentar` nem identidade. Permanecem intactas, entre outras, as regras de superfície
do recurso de tela:

- **`BR-E-23`** — `src/static/` continua proibida, e o teste que falha se um recurso cair numa pasta
  estática continua passando.
- **`BR-E-01..06`** — as rotas de arte continuam com o mesmo contrato (200, mimetype, 404 para ausência,
  ETag).
- A renderização do diagrama **no cliente**, com `securityLevel: 'strict'` (`ADR-03`).
- A ordem das folhas e o `--bs-*` redefinido pela folha própria.

## 4. Modificadas

- **A afirmação de que a tela busca os assets em CDN** (`_reversa_sdd/architecture.md` §1 e §6,
  `c4-context.md`, `c4-containers.md`) **deixa de valer**: não há mais tráfego de saída para terceiros.
  Não é regra de negócio; é fato arquitetural que a próxima extração precisa reescrever.
- **A versão do Mermaid** deixou de ser a faixa `10` e passou a ser fixa em `10.9.8` — atualizar virou
  ato deliberado, com `sha256` declarado.
- **A tela mudou de bytes** (não de pixels): `SHA_DA_TELA` novo, com declaração no adendo e evidência em
  `evidence/SHA_DA_TELA.md`.
