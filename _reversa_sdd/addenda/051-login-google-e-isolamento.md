# Adendo: o sistema passou a exigir identidade, e o dono virou escopo

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-27`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/permissions.md` e
> `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-27.

## Resumo da entrega

O sistema analisava árvore e DNA sem nenhuma identidade: quem alcançasse a porta entrava, e a chave de
conteúdo entregue no formulário decidia qual árvore abria. A entrega põe a conta Google como identidade
de entrada — fluxo OAuth 2.0 feito no projeto, com `state` de uso único e troca de código no servidor — e
transforma o campo `dono`, que era costura de assinatura sem comportamento, no **escopo efetivo** do
armazenamento e do histórico: cada conta tem a própria pasta, e o recurso de outro dono responde como
inexistente (`404`, nunca `403`).

Os dados anteriores à identidade — os 13 arquivos da raiz, os 3 aposentados e o histórico com
`owner_id = 'unico'` — são **copiados** (nunca movidos) para a pasta da conta declarada em
`ANALISADOR_DONO_INICIAL`, no primeiro login dela, com marcador `.dono-inicial`; a segunda execução é
no-op e nenhum arquivo é apagado.

Sem as cinco variáveis de ambiente, o **servidor não sobe** — credencial ausente não degrada para acesso
aberto. A suíte e o invólucro de paridade continuam rodando sem credencial porque a autenticação é
injetável em `create_app`, e é nesse caminho (sem sessão) que o dono legado `"unico"` mantém a pasta
plana.

**36 de 36 ações concluídas.** Suíte: **1.745 passam / 9 pulados / 4 falham**, e as 4 falhas são
pré-existentes (`test_characterization_mermaid`, vermelhas no `HEAD` limpo). Paridade: **30
divergências**, o mesmo número da linha de base da 049/050. São **32 testes novos**, incluindo o teste
negativo A→B que é portão da entrega.

Duas coisas ficam declaradas: o dono legado `"unico"` continua na **raiz** da pasta de upload, e só ele
(é o espaço que existe sem sessão, e é o que mantém 1.718 testes e a paridade sem ajuste); e a **decisão
de arquitetura** está registrada neste adendo, não em um `adrs/39` — o `ADR-39` nasce na próxima
re-extração, junto com a reescrita de `permissions.md`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (visão geral / borda) | `contrato-alterado` | As sete operações de dado passam por guarda de sessão; `_dono()` substitui o literal `DONO_DO_PROCESSO` nas oito chamadas; referência que não resolve responde `404` |
| `_reversa_sdd/architecture.md` | §2 (containers e concorrência) | `delta-de-contrato-externo` | Entram a sessão em cookie e o provedor de identidade como dependência de rede; a reserva de memória e o cache não mudam |
| `_reversa_sdd/architecture.md` | §3 (componentes e pacotes) | `componente-novo` | Entram `web/sessao.py`, `web/autenticacao.py`, `web/rotas_auth.py` e `application/dono_inicial.py`; a tela deixa de ser um template único (`login.html` é o segundo) |
| `_reversa_sdd/architecture.md` | §4 (onde o dado vive) | `delta-de-dados` | O disco ganha pasta por dono, `_aposentados` por dono e o marcador `.dono-inicial`; a sessão vive no cliente, assinada |
| `_reversa_sdd/architecture.md` | §6 (integrações externas) | `componente-novo` | **A afirmação "nenhuma integração de rede com terceiros" deixa de valer**: o Google entra como provedor de identidade (saída HTTPS) |
| `_reversa_sdd/architecture.md` | §7 (dívidas) | `regra-alterada` | A dívida #4 (ausência de isolamento) fecha; a #3 (corrida sobre o disco) continua aberta |
| `_reversa_sdd/architecture.md` | §8 (decisões) | `regra-nova` | A decisão da entrada e do escopo por `sub` passa a valer; o `ADR-39` correspondente é da próxima re-extração |
| `_reversa_sdd/permissions.md` | §1.1 (`dono` existe e não isola) | `regra-alterada` | O `dono` deixou de ser costura: é o `sub` do provedor e escopa listagem, leitura e aposentadoria. Leia "não isola" como **histórico** |
| `_reversa_sdd/permissions.md` | §3 (matriz de permissões) | `regra-alterada` | A matriz deixa de ser degenerada: "ler arquivo de outro dono" passa a ❌, com `404` indistinguível de inexistente; as três rotas de arte continuam públicas |
| `_reversa_sdd/permissions.md` | §4.3 (cobertura) | `regra-alterada` | Autenticação e autorização/propriedade passam a ✅; a chave de conteúdo deixa de ser portadora do acesso e vira endereço dentro do escopo |
| `_reversa_sdd/permissions.md` | §5 e §6 (`P-01`, aceite de risco) | `regra-removida` | `P-01` fecha: a correção da Onda 3 foi executada. O aceite de risco single-tenant do `BUG-20260929-BJJH` deixa de valer, condicionado ao teste negativo verde |
| `_reversa_sdd/domain.md` | §3.5 (upload e armazenamento) | `regra-alterada` | A deduplicação por conteúdo passa a valer **dentro do dono**: o mesmo conteúdo por dois donos são dois arquivos (`RN-05`) |
| `_reversa_sdd/domain.md` | §3.6 (tela de entrada) | `regra-alterada` | A lista é escopada pelo dono; a conta e o comando de sair entram na masthead |
| `_reversa_sdd/domain.md` | §3.7 (histórico) | `regra-alterada` | O histórico grava o `sub` real e toda leitura passa a ser escopada |
| `_reversa_sdd/domain.md` | §5 (contrato de mensagens) | `regra-nova` | Entram 7 literais novos — `Entrar com Google`, a frase da tela de entrada, as três falhas de entrada e `Sair` —; os 29 catalogados continuam intactos, e a recusa por dono alheio reaproveita o literal de inexistência |
| `_reversa_sdd/domain.md` | §6.3 (decisões humanas) | `regra-alterada` | A decisão "não corrigir o isolamento no legado" foi executada na Onda 3: leia como cumprida, não como vigente |
| `_reversa_sdd/state-machines.md` | (máquina nova) | `regra-nova` | Passa a existir o ciclo da sessão — anônimo, autenticado, expirado e encerrado —, com `state` de uso único na transição de entrada |
| `_reversa_sdd/erd-complete.md` | E-06 (`owner_id` sem consulta) | `presença` | A lacuna continua aberta: a coluna segue `TEXT` e sem FK, agora com o conteúdo certo (o `sub`). Não leia como fechada |
| `_reversa_sdd/data-dictionary.md` | `dna_analysis.owner_id` | `delta-de-dados` | A descrição "marcador único de processo, não filtra" deixa de valer: é o `sub` do provedor e o escopo de leitura e escrita |
| `_reversa_sdd/inventory.md` | §4 (pontos de entrada e configuração) | `delta-de-contrato-externo` | Entram as três rotas de entrada e as cinco variáveis obrigatórias; a subida recusa sem elas |
| `_reversa_sdd/c4-context.md` | persona e sistemas externos | `regra-alterada` | A persona deixa de ser "sem login e sem sessão"; o Google entra como o primeiro sistema externo do contexto |
| `_reversa_sdd/addenda/049-sistema-de-log.md` | auditoria | `regra-alterada` | O conjunto fechado de ações ganha `entrar` e `sair`, e a linha ganha o campo `conta` (o `sub`, nunca o e-mail) |

## Regras sob vigilância

`W001` a `W010` — em `_reversa_forward/051-login-google-e-isolamento/regression-watch.md`.

## Fontes

- `_reversa_forward/051-login-google-e-isolamento/legacy-impact.md`
- `_reversa_forward/051-login-google-e-isolamento/regression-watch.md`
- `_reversa_forward/051-login-google-e-isolamento/requirements.md`
- `_reversa_forward/051-login-google-e-isolamento/roadmap.md`
- `_reversa_forward/051-login-google-e-isolamento/actions.md` (36 de 36 ações concluídas)
- `_reversa_forward/051-login-google-e-isolamento/progress.jsonl` (36 eventos)
- `_reversa_forward/051-login-google-e-isolamento/data-delta.md`
- `_reversa_forward/051-login-google-e-isolamento/onboarding.md`
- `_reversa_forward/051-login-google-e-isolamento/interfaces/entrada-e-sessao.md`
- `_reversa_forward/051-login-google-e-isolamento/interfaces/provedor-de-identidade.md`

## Atualização 2026-10-27

**A tela de entrada passou a exibir a arte do topo.** É o mesmo `/banner.png` da masthead, com o
`alt` da ilustração e `w-75` dentro do cartão de entrada. Nenhum contrato muda: a rota já era
pública (`P-08`) e continua a mesma, e a decisão de não repetir o nome do produto no `alt` é a
mesma da masthead. O teste `tests/test_tela_de_entrada.py::test_a_tela_de_entrada_mostra_a_arte_do_topo`
prende a presença da imagem e do texto alternativo.
