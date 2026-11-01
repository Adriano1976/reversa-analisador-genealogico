# Roadmap: os recursos visuais da tela vêm da própria aplicação

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Requirements: `_reversa_forward/054-embutir-bootstrap-e-mermaid/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é um **delta de proveniência**, não de comportamento: os mesmos bytes que o navegador buscava em dois
hosts de terceiro passam a ser servidos pela própria aplicação, e as quatro tags externas dos dois templates
viram tags locais. O caminho escolhido é o que o projeto já usa para a folha de estilo: arquivo em `src/assets/`,
constante de caminho em `app.py`, rota explícita no Blueprint `assets_bp` — **nada de pasta estática** (`W004`) e
nada de diretório estático do Flask (`RN-07` da feature 009). As fontes são o único item com receita: o CSS do
Google Fonts é baixado, tem as 11 URLs de `woff2` reescritas para caminhos locais e é commitado como
`fontes.css`, com os arquivos de fonte ao lado; os 45 blocos `@font-face`, os `unicode-range` e o
`font-display: swap` ficam intactos, para o navegador baixar exatamente os mesmos subconjuntos de hoje. O
controle de diff visual é exercido: `SHA_DA_TELA` é movido com delta declarado no adendo, e a conferência humana
com a rede desligada é a prova de que o desenho não mudou.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Os arquivos embutidos são biblioteca de terceiro, arte de marca e fonte tipográfica; nenhum dado de genealogia entra no repositório. A conferência usa `SAMPLE_GED` sintético | respeita |
| II. Comportamento observável é preservado em refatoração | É o critério central: mesmos bytes de biblioteca, mesma ordem de carregamento, mesmo `mermaid.initialize`, mesma tipografia. O que muda é a origem da resposta, não a resposta | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada rota nova tem teste de contrato; os testes de lista fechada de rotas são atualizados, não afrouxados; a conferência offline vira evidência | respeita |
| IV. Arestas do grafo são tipadas | Não toca travessia de grafo | n/a |
| V. Toda suposição de genealogia genética cita a fonte | Não toca cM nem heurística de parentesco. A procedência das bibliotecas e das fontes é registrada com versão, `sha256` e licença (`RN-07`) | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Os três arquivos de biblioteca moram em `src/assets/`, ao lado de `app.css`, `banner-da-tela.png`, `favicon.png` e `apple-touch-icon.png` | É a única pasta de recurso que entra na imagem pela lista de permissão do `.dockerignore` (`!src/**`), e o precedente da folha (feature 013) já fixou esse caminho | (a) `src/static/` — proibida por `W004`/`BR-E-23`; (b) `docs/` — responde 200 no host e 404 dentro do contêiner (`L-33`); (c) embutir tudo no HTML — inflaria cada resposta em MB | 🟢 |
| D-02 | As fontes moram em `src/assets/fontes/`, com a folha `src/assets/fontes.css` | Mesma pasta da folha, mesma regra de empacotamento; os `woff2` ficam isolados dos demais recursos | (a) `data:` URI dentro do CSS — +33 % de base64 e nenhum cache por arquivo; (b) fonte de terceiro mantida — `L-01` decidiu embutir | 🟢 |
| D-03 | A entrega é por rotas explícitas no Blueprint `assets_bp`: `GET /bootstrap.css`, `GET /bootstrap.js`, `GET /mermaid.js`, `GET /fontes.css` e `GET /fontes/<arquivo>.woff2` | Segue o contrato que a tela já tem (`/app.css`, `/banner.png`): cada recurso é um contrato nomeado, testável e coberto pelos cabeçalhos de borda. Atende `RN-02` sem criar pasta estática | (a) `flask.send_from_directory` com prefixo — vira servidor estático disfarçado e o `W004` proíbe o desenho; (b) `url_map` dinâmico por prefixo — nasceria público por acidente | 🟢 |
| D-04 | `GET /fontes/<arquivo>.woff2` valida o nome contra um conjunto fechado, derivado da pasta, e recusa o resto com 404 | O nome vem do cliente: sem allowlist haveria leitura de caminho arbitrário. O conjunto é fechado porque a receita gera os 11 arquivos e o teste prende a lista | (a) `<path:...>` com `basename` só — aceitaria qualquer `.woff2` da pasta, inclusive um arquivo futuro sem teste; (b) rota por arquivo (11 rotas) — ruído de contrato | 🟢 |
| D-05 | A folha `fontes.css` é a do Google Fonts, com as 11 URLs reescritas para `/fontes/<arquivo>.woff2`; os 45 blocos, os `unicode-range`, os pesos 400–800 e o `font-display: swap` ficam intactos | Preserva exatamente o comportamento tipográfico de hoje, inclusive o carregamento por subconjunto: o navegador só baixa o `woff2` do intervalo que a página usa | (a) gerar CSS próprio com `font-weight` fixo — mudaria a seleção de pesos; (b) uma fonte variable única sem `unicode-range` — baixaria todos os glifos sempre | 🟢 |
| D-06 | `fontes.css` é referenciado **apenas** pelo `index.html`, no lugar dos três `<link>` do Google (dois `preconnect` e um `stylesheet`) | As telas de identidade não carregam a webfont hoje e a decisão `L-02` mandou preservar a tipografia delas. Um `@font-face` em `app.css` alcançaria as seis telas e mudaria o desenho delas | (a) pôr o `@font-face` em `app.css` — muda seis telas sem declaração; (b) duplicar a folha de fonte nas identidades — idem | 🟢 |
| D-07 | A ordem do `<head>` passa a ser: `/bootstrap.css`, `/fontes.css`, `/app.css`; o tema e o `/mermaid.js` continuam depois | `RF-12`: a folha própria redefine `--bs-*` e precisa vencer o Bootstrap; hoje a folha de fonte vem antes dela e a ordem relativa se mantém | (a) Bootstrap depois de `app.css` — quebraria as variáveis; (b) mover o script do Mermaid para o fim do corpo — mudaria o instante da renderização | 🟢 |
| D-08 | `GET /bootstrap.js` fica no fim do corpo, no mesmo lugar da tag atual, e `GET /mermaid.js` continua no `<head>` | O script do Bootstrap precisa do DOM pronto; o do Mermaid é lido no `<head>` e usado no `DOMContentLoaded`. Trocar de posição mudaria o comportamento, não só a origem | (a) `defer` nos dois — mudaria a ordem de execução em relação aos scripts inline da tela | 🟢 |
| D-09 | As cinco constantes novas seguem o molde de `ESTILO_DA_TELA`: caminho absoluto derivado de `__file__`, publicado em `create_app` e lido pela rota por `current_app.config` | É o ponto que os testes usam para simular arquivo ausente com `monkeypatch.setitem(app.config, ...)`, sem tocar no repositório | (a) caminho fixo dentro da rota — intestável sem mexer em disco | 🟢 |
| D-10 | O tipo de mídia é declarado na rota: `text/css`, `text/javascript` e `font/woff2` | `send_file` sem `mimetype` depende da tabela do sistema e pode sair `application/octet-stream`; a rota da folha já declara `text/css` pelo mesmo motivo | (a) confiar no `guess_type` | 🟢 |
| D-11 | Os endpoints novos entram em `PUBLICOS` (`src/web/sessao.py`) | A lista é fechada e nomeia endpoints; sem isso a tela de entrada, que é servida a quem não tem sessão, perde a folha e o desenho | (a) liberar por prefixo de caminho — proibido pela decisão registrada em `sessao.py` | 🟢 |
| D-12 | Cada recurso sai com `?v=<versão>` na tag do template (`?v=5.3.3`, `?v=10.9.8`, `?v=1` para as fontes) | `send_file` já entrega `ETag`/`304`, mas sem invalidar por versão um arquivo trocado continuaria saindo do cache antigo até o `ETag` ser revalidado. O precedente é `/app.css?v=053` | (a) caminho versionado (`/bootstrap-5.3.3.css`) — mais uma rota por versão; (b) sem versão — aceita cache velho após atualização | 🟡 |
| D-13 | As versões ficam fixas e declaradas: Bootstrap `5.3.3` e Mermaid `10.9.8` (a que o endereço `mermaid@10` resolve hoje) | `RN-03`: a faixa `10` deixaria a versão mudar sem commit. O `sha256` de cada arquivo entra no adendo | (a) manter `@10` — a versão mudaria sozinha; (b) atualizar para a 11 — mudança de comportamento fora do escopo | 🟢 |
| D-14 | A receita de aquisição e de geração das fontes vive em `tests/fontes_da_tela.py`, e o teste `tests/test_fontes_da_tela.py` confere os artefatos **sem rede** | Segue o molde da arte (ADR-29): receita em `tests/`, derivado commitado, teste que prende o derivado. A suíte não pode depender de internet | (a) baixar em *fixture* de teste — quebraria a suíte offline; (b) commit sem receita — ninguém saberia reproduzir | 🟢 |
| D-15 | O adendo da feature declara, para cada arquivo: versão, origem, tamanho, `sha256` e licença; e registra o delta de `SHA_DA_TELA` em bytes | `RN-07` e `RN-08`: procedência auditável e mudança de tela declarada no canal do projeto (`_reversa_sdd/addenda/`) | (a) declarar só no comentário do teste — é o defeito que o próprio arquivo denuncia | 🟢 |

**Medição de 2026-10-31** (jsDelivr e Google Fonts, pelo Python do `.venv`):

| Arquivo | Versão | Bytes | `sha256` (início) |
|---------|--------|------:|-------------------|
| `bootstrap.min.css` | 5.3.3 | 232.803 | `3c8f27e6009ccfd7…` |
| `bootstrap.bundle.min.js` | 5.3.3 | 80.721 | `0833b2e9c3a26c25…` |
| `mermaid.min.js` | 10.9.8 | 3.337.857 | `8d607d7ef1d077a8…` |
| `woff2` (11 arquivos) | — | 201.468 | por arquivo, na receita |
| **Total** | | **3.852.849** (3,67 MiB) | |

## 4. Premissas

Nenhuma. O `requirements.md` não tem marcador `[DÚVIDA]` — as três foram resolvidas na sessão de 2026-10-31.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Blueprint de assets | `_reversa_sdd/c4-components.md#Componentes por unidade` (`assets_bp`, `src/web/rotas_assets.py`) | contrato-novo | Cinco rotas de recurso embutido: três bibliotecas, a folha de fontes e os `woff2` |
| Borda HTTP | `_reversa_sdd/architecture.md#1. Visão Geral da Arquitetura` (`src/app.py`) | componente-alterado | Cinco constantes de caminho e cinco chaves de `config`, no molde de `ESTILO_DA_TELA` |
| Guarda de sessão | `_reversa_sdd/addenda/053-conta-com-senha-e-recuperacao.md` (`src/web/sessao.py`) | contrato-alterado | `PUBLICOS` cresce nomeando os endpoints novos |
| Apresentação — tela principal | `_reversa_sdd/architecture.md#1` (`src/templates/index.html`) | contrato-alterado | Quatro tags externas saem; entram `/bootstrap.css`, `/fontes.css`, `/mermaid.js` e `/bootstrap.js` |
| Apresentação — telas de identidade | `_reversa_sdd/architecture.md#1` (`src/templates/_entrada_base.html`) | contrato-alterado | A tag do Bootstrap aponta para `/bootstrap.css`; nada mais muda |
| Inventário de recursos | `_reversa_sdd/recursos-da-tela/requirements.md#Onde a arte mora, e por que ela é commitada` | componente-novo | `src/assets/` ganha três bibliotecas, `fontes.css` e a pasta `fontes/` |
| Empacotamento | `_reversa_sdd/c4-containers.md#Empacotamento` | contrato-alterado | A imagem cresce ~3,9 MB, cobertos pela lista de permissão vigente |
| Invariante de tela | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | contrato-alterado | Hash novo, com delta e razão declarados no adendo |

## 6. Delta no modelo de dados

Nenhuma entidade, campo, tabela ou migração. Os arquivos embutidos são **recursos de apresentação**, não dados:
não entram no ERD, não passam pelo Postgres e não têm ciclo de vida. O inventário, a procedência e a receita de
regeneração estão em `data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `GET /bootstrap.css`, `GET /bootstrap.js`, `GET /mermaid.js`, `GET /fontes.css`, `GET /fontes/<arquivo>.woff2` | HTTP | `_reversa_forward/054-embutir-bootstrap-e-mermaid/interfaces/recursos-embutidos.md` |

Nenhum contrato é removido: as rotas existentes (`/`, `/app.css`, `/banner.png`, `/apple-touch-icon.png`,
`/favicon.png`, `/descartes.csv`, as de identidade e `/busca`) continuam idênticas.

## 8. Plano de migração

Não há dado a migrar. A "migração" é a troca de proveniência, na ordem abaixo:

1. Baixar os três arquivos das versões de `D-13` e conferir tamanho e `sha256` contra a tabela de medição.
2. Gerar `src/assets/fontes.css` e os 11 `woff2` pela receita de `D-14`, conferindo que o CSS mantém 45 blocos
   `@font-face` e 11 URLs locais.
3. Acrescentar as constantes e as chaves de `config` em `app.py` (`D-09`).
4. Criar as cinco rotas em `src/web/rotas_assets.py` (`D-03`, `D-04`, `D-10`).
5. Acrescentar os endpoints a `PUBLICOS` (`D-11`).
6. Trocar as quatro tags em `index.html` e a tag de `_entrada_base.html` (`D-06`, `D-07`, `D-08`, `D-12`).
7. Atualizar as listas fechadas de rotas dos testes existentes (`test_fabrica_do_app.py`,
   `test_cabecalho_de_enquadramento.py`, `test_sessao_e_guarda.py`, `test_host_permitido.py`) e a verificação no
   contêiner (`verificacao_no_conteiner.py`).
8. Escrever os testes novos do contrato, da receita de fontes e do `sha256`.
9. Recalcular `SHA_DA_TELA`, registrar o delta e a razão no adendo (`D-15`).
10. Rodar a suíte, a paridade e a verificação no contêiner; fazer a conferência humana com a rede desligada e
    gravar a evidência.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A sessão de coding não ter rede para baixar os arquivos | alto | baixo | Medido em 2026-10-31: o Python do `.venv` alcança o jsDelivr e o Google Fonts. Se falhar, o operador baixa os arquivos e o teste de `sha256` confirma que são os certos |
| Os bytes baixados divergirem do oficial (proxy, versão diferente) | alto | baixo | `sha256` medido e fixado na receita; o teste compara com o valor declarado, não com a rede |
| Subconjunto de fonte faltando quebrar glifo de nome estrangeiro | médio | baixo | Os 11 `woff2` do CSS do Google são mantidos integralmente, inclusive cirílico, grego e acentos combinantes |
| Atualizar a biblioteca sem invalidar o cache do navegador | médio | médio | `?v=<versão>` nas tags (`D-12`) e `sha256` declarado no adendo |
| `SHA_DA_TELA` virar rotina de atualização | médio | médio | Delta declarado no adendo com razão e tamanho; a regra `RN-08` fixa que a tela não muda além do `<head>` |
| Primeira carga mais pesada, agora pelo servidor | médio | médio | Medir o total e o tempo; `ETag`/`304` na rebusca; o teto de 4 MB do `requirements.md` |
| Alguém "resolver" com pasta estática no futuro | alto | baixo | O teste que proíbe `src/static/` continua passando e a rota nova não monta diretório estático |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Os cinco recursos respondem 200 com o tipo de mídia certo, sem sessão, e com `X-Frame-Options: DENY`
- [ ] O HTML de `GET /` e o das seis telas de identidade não contêm nenhuma URL de origem externa
- [ ] `sha256` dos três arquivos e dos 11 `woff2` declarados no adendo e conferidos por teste
- [ ] A folha de fontes mantém 45 blocos `@font-face` e aponta para caminhos locais
- [ ] A ordem do `<head>` preserva Bootstrap antes de `app.css`, e o Bootstrap JS continua no fim do corpo
- [ ] `src/static/` continua ausente e o teste que a proíbe continua passando
- [ ] `SHA_DA_TELA` atualizado, com delta em bytes e razão no adendo da feature
- [ ] Verificação dentro do contêiner reporta os recursos embutidos como `OK`
- [ ] Conferência humana com a rede desligada registrada em `evidence/`, sem mudança de desenho

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-31 | Versão inicial gerada por `/reversa-plan` | reversa |
