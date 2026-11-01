# Adendo: a tela deixou de depender de CDN

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/c4-context.md`,
> `_reversa_sdd/c4-containers.md` e `_reversa_sdd/recursos-da-tela/requirements.md`)

## Vigência

Vigente desde 2026-10-31.

## Resumo da entrega

A tela e as telas de identidade baixavam do `cdn.jsdelivr.net` a folha do Bootstrap e, na tela principal,
os scripts do Bootstrap e do Mermaid; a tipografia vinha do Google Fonts. **Sem internet, a tela saía sem
estilo, as três abas não alternavam e o diagrama não desenhava.** A feature embutiu os três arquivos de
biblioteca e as duas famílias de fonte no repositório (`src/assets/`), servindo-os por rotas explícitas do
Blueprint `assets_bp` — o mesmo regime da folha de estilo desde a feature 013, sem pasta estática
(`W004`). As versões ficaram fixas (Bootstrap `5.3.3`, Mermaid `10.9.8`) e o comportamento e o desenho de
hoje foram preservados: mesmas abas, mesmos alertas dispensáveis, mesmo tema, mesmo diagrama com
`securityLevel: 'strict'`, mesma tipografia.

**27 de 27 ações concluídas.** Suíte: **2.002 passam / 9 pulados / 5 falham**, e as cinco falhas são
exatamente as pré-existentes da linha de base. São **94 testes novos**. Paridade: **30 divergências**, o
mesmo número da linha de base — nenhuma nova. Verificação dentro do contêiner: **19 executadas, 0 falhas,
1 pulada** (a gravação no banco, sem `DATABASE_URL`).

A tela mudou de **bytes**, não de pixels: `SHA_DA_TELA` foi de `577a17fd…` (51.612) para `3487986a…`
(51.218, **−394 bytes**), e o delta é só o `<head>` — três tags externas saíram, duas locais entraram.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §1. Visão Geral da Arquitetura | `regra-alterada` | A camada de Apresentação não carrega mais "Bootstrap 5.3.3 e Mermaid 10 por CDN": os recursos são servidos pela própria aplicação |
| `_reversa_sdd/architecture.md` | §6. Mapa de Integrações Externas | `regra-removida` | O elemento "CDN de assets web" **não existe mais**. A frase "o único tráfego de saída é o download dos assets de CDN feito pelo navegador" deixou de valer: não há tráfego de saída para terceiros |
| `_reversa_sdd/c4-context.md` | Legenda dos elementos | `componente-extinto` | O elemento externo "CDN web" sai do diagrama de contexto |
| `_reversa_sdd/c4-containers.md` | Inventário de containers | `regra-alterada` | O container 2 (navegador) não lista mais "Bootstrap 5.3.3 · Mermaid 10 (CDN)"; os arquivos chegam do container 1 |
| `_reversa_sdd/c4-containers.md` | Empacotamento | `regra-alterada` | A imagem cresce ~3,9 MB com os recursos embutidos, cobertos pela lista de permissão vigente; a verificação no contêiner passou a cobri-los (`L-33`) |
| `_reversa_sdd/c4-components.md` | Componentes por unidade (`assets_bp`) | `delta-de-contrato-externo` | Cinco rotas novas: `/bootstrap.css`, `/bootstrap.js`, `/mermaid.js`, `/fontes.css` e `/fontes/<arquivo>.woff2` (esta com conjunto fechado de 11 nomes) |
| `_reversa_sdd/recursos-da-tela/requirements.md` | Onde a arte mora, e por que ela é commitada | `regra-nova` | O regime "arquivo em `src/assets/`, servido por rota própria, `src/static/` proibida" passou a valer também para bibliotecas de front-end e fontes |
| `_reversa_sdd/adrs/03-mermaid-no-cliente.md` | Decisão | `regra-alterada` | A decisão de renderizar o diagrama **no cliente** continua vigente; o que mudou é a procedência do arquivo e a versão, que deixou de ser a faixa `10` e está fixa em `10.9.8` |
| `_reversa_sdd/architecture.md` | §1 (inventário de recursos) | `delta-de-dados` | Entraram 3 bibliotecas, `fontes.css` e 11 `woff2` em `src/assets/`; nenhuma entidade, tabela ou migração |

Nenhuma regra de negócio do `domain.md` mudou: a feature não toca matching, cM, travessia de grafo,
`aposentar` nem identidade.

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005`, `W006`, `W007`, `W008`, `W009`, `W010` — em
`_reversa_forward/054-embutir-bootstrap-e-mermaid/regression-watch.md`.

## Fontes

- `_reversa_forward/054-embutir-bootstrap-e-mermaid/requirements.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/roadmap.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/actions.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/legacy-impact.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/regression-watch.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/procedencia.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/SHA_DA_TELA.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/conferencia.md`
- `_reversa_forward/054-embutir-bootstrap-e-mermaid/evidence/medicoes.md`
