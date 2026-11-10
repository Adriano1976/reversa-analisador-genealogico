# Interface: `POST /grupos.csv`

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Tipo: HTTP (download de arquivo)
> Confidência: 🟡 INFERIDO (mesmo regime de `/descartes.csv`, `RF-16` é `Should`)

## 1. Requisição

```http
POST /grupos.csv HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: session=...
```

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| `dados` | texto (JSON) | sim | Lista de grupos como a tela os tem; JSON inválido é tratado como lista vazia |

**Sessão:** obrigatória, como em `/descartes.csv`.

**Por que escondido no HTML e não recalculado no servidor:** é o padrão vigente da rota de descartes
(`src/web/rotas_assets.py`, `descartes_em_csv`). Recalcular exigiria reler o arquivo de triangulação e refazer
a classificação, o que abriria uma segunda fonte de verdade para o mesmo número.

## 2. Resposta

`200 OK`

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename=grupos.csv
```

**Formato** (o mesmo dialeto de `csv_de_descartes`, pelos mesmos motivos):

- separador `;`, terminador `\r\n`, **BOM** no início;
- decimal com vírgula;
- célula que começa com `=`, `+`, `-` ou `@` recebe `'` na frente, para o Excel não avaliar como fórmula.

| Coluna | Conteúdo |
|--------|----------|
| `Cromossomo` | como veio no arquivo (`7`, `20`) |
| `Início (pb)` | início da interseção |
| `Fim (pb)` | fim da interseção |
| `Extensão (Mb)` | derivada da interseção, duas casas |
| `Kits` | quantidade de membros |
| `cM mínimo` | do par mais fraco |
| `cM máximo` | do par mais forte |
| `Desfecho` | convergente / dividido / parcial / sem ancestral documentado, ou vazio no modo sem árvore |
| `Alerta` | `acúmulo` ou vazio |
| `Membros` | `Nome (KIT)` separados por ` \| ` |
| `Ancestral comum` | nomes dos ancestrais apontados, quando houver |

## 3. Erros

| Situação | Resposta |
|----------|----------|
| `dados` ausente, inválido ou não-lista | `200` com **apenas o cabeçalho** (mesma escolha de `/descartes.csv`) |
| Sem sessão | redirecionamento de entrada |

Não há `404`: a rota não resolve referência de arquivo.

## 4. Idempotência

A rota é pura sobre o corpo recebido: o mesmo `dados` produz o mesmo arquivo, byte a byte. Não grava nada.

## 5. Limites

| Item | Valor |
|------|-------|
| Corpo | o limite vigente da borda (16 MB), suficiente para 200 grupos com dezenas de membros |
| Timeout | o do servidor; a rota não define timeout próprio |
| Chamadas externas | nenhuma |
