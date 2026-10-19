# Regression Watch: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-------------------------------|---------------------|-------------------|
| W001 | `src/templates/index.html`, `h5` do cartão; `RF-01`–`RF-03` | O cabeçalho tem três faixas na ordem título → selos → sinais, e o título mede 1,4 rem | `presença` | O título volta a dividir a linha com os selos, ou a escala muda sem decisão |
| W002 | `src/templates/index.html`, `card-header`; `RN-05` | Nenhum `div` dentro do `card-header` | `ausência` | Um `div` novo trunca os extratores no primeiro `</div>` e as guardas do cartão caem |
| W003 | `src/templates/index.html`, link do retorno; `RF-04` | O link continua `<a class="voltar-ao-indice" href="#resultados">Voltar<span class="visually-hidden">…</span></a>`, sem ícone em markup | `redação` | Um `<svg>`/`<span>` de ícone entra no link, ou o texto muda |
| W004 | `src/assets/app.css`, bloco 036; `RN-07` | As regras novas são escopadas em `.cartao-do-resultado`; "Matches descartados" e "Observações do arquivo" não são alcançados | `ausência` | Uma regra nova muda o losango, a superfície ou o título dos blocos irmãos |
| W005 | `src/assets/app.css`, hover; `RN-09` | `.cartao-do-resultado > summary.sumario-do-cartao:hover{text-decoration:none}` existe e vence a regra global | `presença` | O cabeçalho inteiro volta a sublinhar ao passar o mouse |
| W006 | `tests/test_icone_de_atalho.py`, `SHA_DA_TELA`; `RF-10` | O hash continua `c4a34f7b…`, 30.781 bytes, e o teste verde | `presença` | O hash muda sem mudança de tela declarada |
| W007 | `src/assets/app.css`; `RN-06` | Os quatro estados, o selo de cM (`bg-secondary`, 4,69:1), identidade, validação, janela e profundidade mantêm classes e cores | `presença` | Um selo muda de cor ou de classe, ou o contraste cai |
| W008 | `src/assets/app.css`; `RN-05` | As regras genéricas `details.card > summary.sumario-do-cartao…` e as rotações `45deg`/`-135deg` continuam na folha | `presença` | O losango dos blocos irmãos some ou o indicador deixa de girar |

## Observações

- **OBS-01** 🟡 A conferência visual renderizada (sombra, barra, alinhamento fino) não foi executada
  nesta rodada — sem navegador no loop. A verificação foi por medição (`evidence/depois/cartao.md`);
  o `onboarding.md` passos 4 a 8 cobre o que olhar.
- **OBS-02** 🟡 O working tree já vinha com mudanças não commitadas de rodadas anteriores
  (`src/app.py`, `application/`, `core/`, `parsers/`, `ports/`, `tests/conftest.py` e outros). O
  delta da 036 foi medido contra as cópias de `evidence/antes/` para não misturar as duas coisas.
- **OBS-03** 🟡 O `SHA_DA_TELA` mede a tela **vazia**; uma medição feita com a pasta real de uploads
  devolve 43.064 bytes. O valor válido é 30.781 bytes / `c4a34f7b…`.
- **OBS-04** 🟡 O arranjo final é grid com áreas nomeadas, e não o `flex` do `D-02` do roadmap — o
  ajuste está declarado no `evidence/RELATORIO.md` §3.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|------|-------------|-----------|
| — | — | Aguardando a próxima execução de `/reversa` |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | — | — |
