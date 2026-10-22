# Onboarding: como testar a paginação pela primeira vez

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Para quem nunca viu esta feature: o caminho completo, do zero ao veredito, em cerca de 15 minutos.

## 1. Antes de começar

| Item | Como conferir |
|---|---|
| Interpretador oficial | `.\.venv\Scripts\python.exe --version` → `Python 3.14.x` |
| Dependências | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` (já instalado, se a suíte roda) |
| Um GEDCOM e um CSV reais | em `src/uploads/`. **Nada de `src/uploads/` entra no Git**; o capítulo 5 do `README.md` explica o manifesto e o expurgo |
| Suíte de partida | `.\.venv\Scripts\python.exe -m pytest tests -q` → **1585 passou, 9 pulados** antes desta feature |

## 2. Subir a tela

```powershell
.\.venv\Scripts\python.exe src\app.py
```

O processo imprime `Servindo com waitress em http://0.0.0.0:5000 …`. Abra
<http://127.0.0.1:5000>. **Uma instância só**: se a porta estiver ocupada, o processo anterior está
vivo — não suba outro.

## 3. Produzir uma análise

1. **Fase 1**, escolha o `.ged` na lista e clique em carregar.
2. **Fase 2**, escolha o `.csv` de matches e informe a raiz (o seu nome, como está no GEDCOM).
3. Clique em analisar. No arquivo real desta máquina a análise leva de 12 a 31 s.

Quando terminar, role até **Resultados das Análises de Conexão**.

## 4. O que deve estar na tela

| # | O que olhar | Esperado |
|---|---|---|
| 1 | Quantos cartões aparecem | **10** (ou todos, se a análise tiver 10 ou menos) |
| 2 | O texto do controle | "Página 1 de N", com N = `teto(total / 10)` |
| 3 | A frase do topo | continua dizendo **o total** de conexões analisadas, não 10 |
| 4 | Os números das páginas | N botões; o **1** está marcado como corrente |
| 5 | "Anterior" | **desabilitado** na página 1 |
| 6 | Os cartões 11 a 68 | continuam no documento, com `hidden` |

Para conferir os itens 1 e 6 no console do navegador (F12):

```js
document.querySelectorAll("details.cartao-do-resultado").length            // 68
document.querySelectorAll("details.cartao-do-resultado:not([hidden])").length // 10
```

## 5. Trocar o tamanho

1. Escolha **20** no seletor → os cartões 1 a 20 visíveis, "Página 1 de 4".
2. Escolha **30** → "Página 1 de 3".
3. Volte para **10** → "Página 1 de 7".

A troca é **local**: o console (aba Network) não registra requisição nenhuma.

## 6. Navegar

1. Clique em **Próxima** → cartões 11 a 20; a lista volta para o topo dos resultados.
2. Clique no **7** → "Página 7 de 7" e **8 cartões** (o resto), com "Próxima" desabilitada.
3. Abra um cartão na página 7 e clique em **Voltar** → a tela rola até o título e **continua na
   página 7**.

## 7. O link direto

Com a barra de endereços:

```
http://127.0.0.1:5000/#resultado-37
```

Esperado: a tela abre na **página 4** (cartões 31 a 40) e o cartão **37 aberto**, com o diagrama
desenhado. Se o diagrama vier com altura zero, a ordem "mostrar a página, depois abrir" foi
invertida (`D-07` do `roadmap.md`) — é o defeito que a decisão existe para evitar.

## 8. Os botões de expandir e recolher

1. Na página 2, clique em **Expandir todas as análises** → exatamente **10** cartões abrem.
2. Volte para a página 1 → os cartões dela continuam como estavam.

## 9. A degradação sem script

Desligue o JavaScript do navegador e recarregue a análise. Esperado: **todos os cartões em
sequência**, sem controle de paginação. É o comportamento anterior a esta feature — e é o que
garante que ninguém perde conteúdo por falta de script.

## 10. A consequência que precisa ser vista uma vez

Com a paginação ativa, procure (Ctrl+F) o nome de uma conexão que esteja **na página 5**. Ele **não
é encontrado**. Não é defeito de implementação: o texto está no documento, mas `hidden` o tira da
busca do navegador. Está registrado em `requirements.md` §10 e no `roadmap.md` §9. A resposta
definitiva para "achar um nome" seria busca/filtro, que não é esta feature.

## 11. Fechar o ciclo

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
git status --porcelain
```

- A suíte deve ficar verde, com a baseline de 1585/9 **mais** os testes novos de
  `tests/test_paginacao_na_tela.py`.
- Se `test_icone_de_atalho.py` falhar com "a tela mudou", a mudança é **esperada**: o `<script>`
  novo entra no que o hash mede. Atualize `SHA_DA_TELA` e `TAMANHO_ESPERADO` com o valor medido e
  registre a mudança em `legacy-impact.md` — nunca ajuste o número só para o teste passar.
- `git status` deve mostrar **apenas** `src/`, `tests/` e a pasta da feature. Nenhum arquivo de
  `src/uploads/` pode aparecer.

## 12. Se algo der errado

| Sintoma | Onde olhar primeiro |
|---|---|
| Todos os cartões aparecem de uma vez | o `<nav>` não foi renderizado (a guarda de `total_de_paginas > 1` comeu o bloco) |
| Cartões de outra página aparecem | regra `details.cartao-do-resultado[hidden]` ausente na folha, e um `display` venceu o atributo |
| O diagrama de um cartão fica sem altura | ordem mostrar/abrir invertida, ou cartão aberto enquanto escondido |
| O contador do topo virou "10" | alguém trocou `dna_results \| length` pelo tamanho da página |
| "Próxima" não desabilita na última página | o `Math.ceil` do total de páginas não está sendo recalculado quando o tamanho muda |
