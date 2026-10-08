# Onboarding: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Para: quem vai testar esta feature pela primeira vez, com o stack no ar
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 0. O que você vai provar

Cinco afirmações, nesta ordem. As quatro primeiras são mecânicas; a **quinta só você pode
provar**, porque depende de um aparelho.

1. O caminho `/apple-touch-icon.png` **respondia `404` antes** e responde `200` depois.
2. A imagem servida tem **180×180** e **nenhum pixel transparente**.
3. Ela existe **dentro do contêiner**, não só na máquina de desenvolvimento.
4. A tela (`GET /`) **não mudou** — nem um byte.
5. No celular, o atalho salvo na tela inicial mostra **o logo do projeto**.

## 1. Pré-requisitos

| Item | Como conferir |
|---|---|
| Docker Desktop no ar | `docker info --format '{{.ServerVersion}}'` responde uma versão |
| O `.env` da raiz existe | `Test-Path .env` → `True`. Ele é **gitignored** e não é criado por este documento |
| Interpretador oficial para as sondas | `.\.venv\Scripts\python.exe` |
| A biblioteca de imagem, para a sonda do passo 4 | já está no `.venv/` (Pillow). **Não** está em `requirements.txt`, que é a lista de runtime (`D-09`) |

> Todos os comandos abaixo são para **PowerShell na raiz do projeto**.

## 2. Linha de base — faça isto **antes** de aplicar a feature

Se você está conferindo a entrega já feita, este passo pode ser pulado: ele existe para provar
o "falha antes" do `RF-08`.

```powershell
docker compose up -d
curl.exe -s -o NUL -w "apple-touch-icon  -> %{http_code}`n" http://127.0.0.1:5080/apple-touch-icon.png
curl.exe -s -o NUL -w "precomposed       -> %{http_code}`n" http://127.0.0.1:5080/apple-touch-icon-precomposed.png
curl.exe -s -o NUL -w "favicon.ico       -> %{http_code}`n" http://127.0.0.1:5080/favicon.ico
curl.exe -s -o NUL -w "raiz              -> %{http_code}`n" http://127.0.0.1:5080/
```

**Esperado antes da feature:** `404`, `404`, `404`, `200`.
Guardadas as três medidas da raiz, você tem a linha de base do passo 5:

```powershell
(Invoke-WebRequest http://127.0.0.1:5080/).Content.Length
```

## 3. Aplicar e subir

A arte de runtime é **commitada** (`D-02`), então não há passo de geração a executar. O que
existe é a reconstrução da imagem, porque o `src/` é **assado** nela:

```powershell
docker compose up -d --build app
```

> A reconstrução leva de um a três minutos. A primeira execução depois dela pode responder
> `502` por alguns segundos, enquanto o processo sobe.

## 4. Provar a imagem servida

```powershell
$r = Invoke-WebRequest http://127.0.0.1:5080/apple-touch-icon.png
"status      : $($r.StatusCode)"
"content-type: $($r.Headers['Content-Type'])"
"bytes       : $($r.RawContentLength)"
"etag        : $($r.Headers['ETag'])"
"last-modified: $($r.Headers['Last-Modified'])"
$r.Content | Set-Content -Encoding Byte -Path icone-servido.png
```

Agora a sonda de conteúdo — dimensão, opacidade e cor dos cantos:

```powershell
.\.venv\Scripts\python.exe -c @"
from PIL import Image
im = Image.open('icone-servido.png')
print('dimensoes :', im.size)
a = im.convert('RGBA').getchannel('A')
print('alpha     :', a.getextrema())
c = im.convert('RGB')
print('cantos    :', [c.getpixel(p) for p in [(0,0),(179,0),(0,179),(179,179)]])
"@
```

**Esperado:**

| Medida | Valor |
|---|---|
| `dimensoes` | `(180, 180)` |
| `alpha` | `(255, 255)` — nenhum pixel transparente |
| `cantos` | os quatro iguais a `(255, 255, 255)` |

Se `alpha` vier `(0, 255)` ou qualquer mínimo abaixo de `255`, a arte **não** foi composta
sobre branco — é o defeito que a `RN-04` existe para evitar, e o atalho ficaria com fundo preto.

## 5. Provar a revalidação e a imutabilidade da tela

```powershell
# revalidacao: a segunda busca devolve "nao modificado", sem corpo
$e = (Invoke-WebRequest http://127.0.0.1:5080/apple-touch-icon.png).Headers['ETag']
$r2 = Invoke-WebRequest http://127.0.0.1:5080/apple-touch-icon.png -Headers @{ 'If-None-Match' = $e }
"revalidacao: $($r2.StatusCode)  bytes=$($r2.RawContentLength)"
"cache-control presente: $([bool]$r2.Headers['Cache-Control'])"
```

**Esperado:** `304` com `0` bytes, e **nenhuma** validade longa declarada.

```powershell
# a tela nao mudou: compare com o numero guardado no passo 2
"raiz agora: $((Invoke-WebRequest http://127.0.0.1:5080/).Content.Length)"
```

**Esperado:** exatamente o mesmo número do passo 2. Divergiu → `RF-05` falhou, e é bloqueio.

## 6. Provar que existe **dentro** do contêiner

Este é o passo que pega a falha silenciosa do `RF-04`: a rota pode responder `200` no host,
servida de um arquivo fora do contexto de build, e responder `404` na imagem publicada.

```powershell
docker compose exec -T app ls -l /app/src/assets
```

**Esperado:** o arquivo listado. Se ele não estiver lá, a causa é a pasta escolhida — e `D-03`
diz qual ela tem de ser.

Opcional, e a prova mais direta de que a rota responde **de dentro**: use o **próprio
interpretador do contêiner**, porque a imagem é `python:3.14-slim` e **não** traz `wget` nem
`curl` (medido no `docker/Dockerfile`). Repare que a porta lá dentro é a **do contêiner**, não a
`5080` publicada no host:

```powershell
docker compose exec -T app python -c 'import urllib.request as u; r=u.urlopen("http://127.0.0.1:5000/apple-touch-icon.png"); print(r.status, r.headers.get("Content-Type"), len(r.read()))'
```

**Esperado:** `200 image/png 16504`. Esse número **não** é decorado: é a receita de `D-02`
executada e medida — arte canônica composta sobre branco, redimensionada para 180×180 com
reamostragem de alta qualidade e salva como PNG otimizado dá **16.504 bytes**. É 21 % menor que
os 20.954 bytes da mesma arte **transparente**, porque o fundo branco chapado comprime muito
melhor. Se vier um tamanho muito diferente, confira a receita antes de suspeitar da rota.

Se esta linha responder `404` enquanto o passo 4 respondeu `200`, a arte está no host e **não**
na imagem: é exatamente a falha silenciosa que o `RF-04` existe para pegar.

## 7. Provar que `src/static/` continua ausente

```powershell
"src/static existe: $(Test-Path src\static)"
```

**Esperado:** `False`. Virou `True` → o `W004` foi reaberto, e é bloqueio.

## 8. A prova que só você pode fazer — no celular

Os passos acima provam que a **resposta** está certa. Eles **não** provam que o sistema móvel a
usa. Isso depende de aparelho, e é a lacuna declarada em `investigation.md` §6.

1. Ponha o celular **na mesma rede** da máquina e descubra o IP dela (`ipconfig`).
2. Suba o stack com a aplicação acessível na rede, e **não** só no `loopback`:
   a publicação de porta do `docker-compose.yml` está fixada em `127.0.0.1`, então este teste
   exige alterá-la para `0.0.0.0` **na sua máquina**, e desfazer depois.
   ⚠️ Enquanto estiver assim, **qualquer pessoa da rede alcança a aplicação** — e o sistema
   continua sem autenticação e single-tenant (`BUG-20260929-BJJH`, dívida #4 aberta). Faça o
   teste, salve o atalho e **volte a porta para `127.0.0.1`**.
3. Abra `http://<ip-da-maquina>:5080/` no navegador do celular.
4. Salve na tela inicial.
5. Confira o ícone.

### Se o atalho continuar com o ícone antigo

**Esperado, e não é defeito.** O sistema guarda o ícone do atalho de forma agressiva e **ignora
os cabeçalhos** nesse ponto. Procedimento: **remova o atalho**, limpe os dados do navegador para
esse endereço, e salve de novo. Em alguns aparelhos é preciso reiniciar.

## 9. Diagnóstico

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `404` na `5080`, mas `200` no host | A arte ficou fora do contexto de build | `D-03`: o arquivo tem de estar sob `src/`. Confira o `.dockerignore` |
| `200`, mas `alpha` com mínimo abaixo de `255` | A arte foi servida transparente | `RN-04`: recomposta sobre branco, 180×180 |
| `200`, mas dimensão diferente de `180×180` | Arte regerada com outro tamanho | Regere com 180 (`D-02`) |
| A raiz mudou de tamanho | Alguém tocou no template | `RF-05`: bloqueio. O template não faz parte desta feature |
| `src/static` existe | Pasta proibida reaberta | `W004`: bloqueio. Remova e sirva pela rota |
| Teste de deriva falhando | Arte de runtime e canônica divergiram de verdade | Regere a derivada a partir de `docs/assets/img/logo.png` |
| Teste de deriva falhando **sem** ninguém ter mexido na arte | Comparação por bytes em vez de pixel | `D-08`: o teste **regenera** e compara pixel a pixel |

## 10. Encerrar

```powershell
docker compose down            # preserva os volumes e src/uploads/
Remove-Item icone-servido.png -ErrorAction SilentlyContinue
git status --short             # nao pode listar src/uploads/ nem o .env
```

> `down` **sem** `-v` preserva o volume do banco e o *bind mount* de `src/uploads/`. Use `-v`
> apenas se quiser apagar o histórico do banco.

## 11. Fontes

- `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md` (`RF-01` a `RF-11`)
- `_reversa_forward/009-rota-do-apple-touch-icon/roadmap.md` (`D-02`, `D-03`, `D-08`, `D-09`)
- `_reversa_forward/009-rota-do-apple-touch-icon/interfaces/apple-touch-icon.md` (o contrato)
- `_reversa_forward/008-persistencia-postgres-docker/onboarding.md` (o formato e os comandos de
  stack desta casa, dos quais os passos 3 e 10 são continuação)
