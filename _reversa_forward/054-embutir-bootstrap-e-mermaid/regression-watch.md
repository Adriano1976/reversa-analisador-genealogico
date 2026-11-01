# Regression watch — feature 054

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Base: seção "Modificadas" de `legacy-impact.md`

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/architecture.md` §6 (Mapa de Integrações Externas) | Nenhum documento servido pela aplicação referencia host externo em `link`, `preconnect` ou `script` | `ausência` | Qualquer tag com `https://` no HTML de `GET /` ou das telas de identidade |
| W002 | `_reversa_sdd/c4-context.md` (elemento "CDN web") | O elemento externo "CDN web" não existe mais; Bootstrap, Mermaid e fontes são servidos pela aplicação | `presença` | `cdn.jsdelivr.net`, `fonts.googleapis.com` ou `fonts.gstatic.com` em qualquer resposta |
| W003 | `_reversa_sdd/adrs/03-mermaid-no-cliente.md` | O diagrama continua sendo renderizado no navegador, com `securityLevel: 'strict'`, e agora o arquivo vem de `/mermaid.js` | `presença` | `securityLevel` diferente de `strict`, ou o script deixar de ser servido pela aplicação |
| W004 | `src/templates/index.html` (ordem do `<head>`) | `/bootstrap.css` antes de `/fontes.css`, que vem antes de `/app.css` | `redação` | A folha própria deixar de vencer as variáveis `--bs-*` |
| W005 | `src/templates/index.html` (posição dos scripts) | `/mermaid.js` no `<head>` e `/bootstrap.js` como último script com `src` | `redação` | Mermaid movido para o fim do corpo, ou Bootstrap antes do conteúdo |
| W006 | `src/web/rotas_assets.py` (`FONTES_DA_TELA`) | O conjunto de nomes aceitos em `/fontes/<arquivo>.woff2` é fechado e igual ao das fontes commitadas | `presença` | Nome de fonte novo em disco sem entrar no conjunto, ou conjunto aceitando nome fora da pasta |
| W007 | `_reversa_sdd/recursos-da-tela/requirements.md` (`W004`/`BR-E-23`) | `src/static/` continua ausente e nenhum recurso é servido por diretório estático | `ausência` | A pasta reaparecer, ou uma rota montar diretório estático |
| W008 | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | O hash da tela de entrada só muda com declaração em `_reversa_sdd/addenda/` e delta registrado | `presença` | Hash diferente do declarado sem adendo correspondente |
| W009 | `src/templates/_entrada_base.html` (telas de identidade) | As telas de identidade não carregam a webfont e mantêm a tipografia nativa | `ausência` | `/fontes.css` aparecer no HTML de `/login`, `/cadastro` ou `/recuperacao` |
| W010 | `_reversa_sdd/c4-containers.md` §Empacotamento | Os arquivos embutidos entram na imagem pela lista de permissão e respondem dentro do contêiner | `presença` | `FALHA` na verificação no contêiner para uma das rotas de recurso |

## Observações (sem peso de regressão)

- 🟡 O teto de 4 MB para a soma dos arquivos embutidos é uma **decisão**, não uma medição de limite
  técnico; hoje a soma é 3.868.413 bytes. Se o Mermaid ganhar versão muito maior, a decisão precisa
  ser revista em vez de o teste afrouxado.
- 🟡 `?v=` nas tags é conveniência de cache, não correção: um arquivo trocado sem revalidação continua
  saindo do cache até o `ETag` ser conferido.
- 🟡 A conferência visual com a rede desligada depende de humano; o registro automatizável está em
  `evidence/conferencia.md`, e o olho no desenho fica para o operador.

## Histórico de re-extrações

<!-- Preenchido pelo agente reverso quando /reversa rodar de novo sobre este código. -->

## Arquivadas

<!-- Itens arquivados após três verificações verdes consecutivas. -->
