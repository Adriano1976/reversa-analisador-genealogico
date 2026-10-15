# Moldura do cartão: veredicto do doador e diagrama recolhido

**Data:** 2026-10-14
**Tipo:** **apresentação**. Não altera decisão de matching, caminho, estado do documental, cM,
veredito nem a ordem dos cartões.
**Arquivos alterados:** `src/templates/index.html`, `src/assets/app.css`,
`tests/test_estado_do_resultado.py` (não), `tests/test_estilo_da_tela.py`,
`tests/test_profundidade_do_caminho.py`, `tests/test_icone_de_atalho.py`, `README.md`
**Declaração da mudança de tela:** `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md`
**Teste novo:** `tests/test_profundidade_do_caminho.py::TestOCartaoDoDoadorImpossivel` (9 testes)

> Este arquivo é o **log de trabalho**. A declaração formal da mudança de tela — que é o canal que
> autoriza a troca do `SHA_DA_TELA` — está no adendo `015`. Aqui fica o que foi medido antes de
> decidir.

## A proposta do operador, e o que ela custava

*"Todas as pessoas que tivessem um caminho genealógico no GEDCOM, mas com janela de vida acusando,
fossem classificadas como 'Parentesco documental não encontrado', como as outras — ficaria melhor do
que apresentar um gráfico inconsistente?"*

Medido com `_reversa_bugs/_sondas-matching/avaliar_regra_nao_encontrado.py`:

```
alcança .................. 3 cartões de 62  (TG8027863, ZC1171551, ZL6373425)
perde .................... a ÚNICA comparação de cM da análise
                           (TG8027863 sai de COMPATIVEL para INCONCLUSIVO)
perde .................... 1 dos 5 cartões que apontam para o mesmo ancestral
afirma ................... "nenhum caminho genealógico foi encontrado no GEDCOM"
                           — FALSO: a árvore tem o caminho, em 11, 12 e 10 meioses
```

A frase falsa não é detalhe de redação: ela manda o operador procurar **registro faltando** quando o
trabalho é procurar **homônimo**.

## O que foi feito, então

A queixa — "um gráfico inconsistente" — é legítima, e o alvo dela é a **moldura**, não o dado:

1. o cartão **abre** com *"Nenhum parentesco atribuível ao doador"*, dizendo que a árvore **tem** o
   caminho e que o vínculo entre o DNA e a árvore continua desconhecido;
2. o parentesco passa a ser apresentado como **do registro escolhido** — nos 62 cartões, e não só
   nos 3, porque em 9 deles a identidade já é `a_confirmar` e o rótulo antigo também afirmava demais;
3. o diagrama fica em `<details>`, **recolhido** quando a janela é impossível, com o título
   *"Caminho do registro escolhido no GEDCOM — não é o caminho do doador"*.

## O que o recolhimento exigiu, e o que eu NÃO consegui verificar

O Mermaid mede o container para dimensionar o SVG. Dentro de um `<details>` fechado o elemento tem
tamanho zero — o desenho sai quebrado e o nó fica marcado como `data-processed`, então **abrir depois
não conserta**. A rodada inicial passou a pular o que está em `details` fechado, e o `toggle`
renderiza na primeira abertura.

**A renderização em navegador não foi verificada** — só o HTML, o filtro, o listener e a guarda, que
estão presos por teste. É a dívida declarada no adendo `015`, e o recuo é uma linha.

## Um erro meu no caminho

Ao anexar os testes, abri o arquivo em modo **append** e gravei apenas o bloco novo: as duas
substituições anteriores (promover `_pagina` a função de módulo e fazer o método delegar) **nunca
foram escritas**. Os testes acusaram com `NameError: name '_pagina' is not defined` — o sintoma
apontava para o teste, e a causa estava no script que o gerou. Padrão a repetir: quando o script faz
leitura, transformação e escrita, a escrita tem de ser do texto **transformado**, e não só do pedaço
anexado.

## Verificação

- **943 testes, zero falhas** (934 → 943; 9 novos).
- O `SHA_DA_TELA` mudou (28.858 → 29.486 bytes) porque o `<script>` global mudou — o conteúdo
  **visível** da tela de entrada vazia é o mesmo. Registrado no adendo, que é o canal de declaração.
- Medido no HTML servido pelo processo no ar, na análise real de 62 cartões:

```
veredicto do doador (blocos) ......... 3
"Parentesco do registro escolhido:" .. 62
"Parentesco encontrado:" ............. 0
details do diagrama .................. 11   (3 recolhidos, 8 abertos)
"não é o caminho do doador" .......... 3
```

E o texto exato, nos dois casos que importam:

| Cartão | Veredicto | `<details>` | Título |
|---|---|---|---|
| Manoel da Silva Vieira (233 anos) | presente | **recolhido** | Caminho do registro escolhido no GEDCOM — não é o caminho do doador |
| Eline Cabral Vieira Vasconcelos | ausente | aberto | Caminho genealógico no GEDCOM |
