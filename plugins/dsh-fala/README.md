# dsh-fala

Plugin do DeepSeek Harness que lê em voz alta o desfecho de cada turno **na sessão em que `/fala-on` foi chamado**, e fica muda em todas as outras.

É o porte do mod `fala` do Claude Code (`CLAUDE CODE SPEAK MOD`) para os pontos de extensão nativos do harness: `ctx.commands.register` para os comandos por sessão e o firehose `session/event` para saber quando um turno terminou.

## Comandos

| Comando | Efeito |
| --- | --- |
| `/fala-on` | Liga a voz nesta sessão. Responde `Voz ligada nesta sessão.` |
| `/fala-off` | Desliga a voz nesta sessão. Responde `Voz desligada nesta sessão.` |

Toda sessão nova começa muda: o estado vive só na memória do processo, então reiniciar o harness também volta tudo ao mudo.

## O que é falado

- Só o turno que termina com `completed` — turno abortado, com erro, bloqueado ou sem prosa visível não fala.
- Só o texto visível do último `assistant/message` do turno: reasoning e blocos de ferramenta ficam mudos.
- Markdown é reduzido a prosa (sem cercas de código, sem `*`, sem links) e cortado em 4.000 caracteres.
- As falas entram numa fila: cada resposta só toca depois que a anterior terminou.

## Pré-requisitos (Windows)

1. `edge-tts` no Python: `python -m pip install edge-tts`. O plugin chama `edge-tts` do PATH e, se ele não existir, cai para `python -m edge_tts` — que é o caso quando o pip instala em `%APPDATA%\Python\Python314\Scripts` (fora do PATH).
2. `ffplay` no PATH (`winget install Gyan.FFmpeg`).
3. Rede: o edge-tts sintetiza no serviço da Microsoft.

Teste rápido:

```powershell
python -m edge_tts --voice pt-BR-ThalitaMultilingualNeural --text "teste" --write-media teste.mp3
ffplay -nodisp -autoexit -loglevel quiet teste.mp3
```

## Instalação no perfil

O pacote é ligado ao perfil por junction e habilitado no patch do perfil:

```powershell
$link = "$env:USERPROFILE\.dsh\profiles\web\node_modules\dsh-fala"
New-Item -ItemType Junction -Path $link -Target "D:\Projetos\reversa_analisador_gelealogico\plugins\dsh-fala"
```

E, em `%USERPROFILE%\.dsh\profiles\web\cordis.patch.yml`:

```yaml
- insert:
    - id: fala
      name: 'dsh-fala'
```

Como o perfil web declara `patchReload: live`, editar o patch recarrega o plugin; se o comando não aparecer no menu `/`, reinicie o harness.

## Desenvolvimento

```powershell
node smoke.mjs
```

O teste de fumaça monta um contexto Cordis falso, liga o plugin em modo de ensaio (`dryRun`) e confere as regras: sessão nova muda, `/fala-on` liga só aquela sessão, `/fala-off` desliga, turno abortado/com erro/sem texto não fala, texto longo é cortado.

## Estrutura

- `lib/index.js` — o plugin (comandos, buffer do turno, fila de fala, edge-tts + ffplay).
- `smoke.mjs` — teste de fumaça sem áudio.
