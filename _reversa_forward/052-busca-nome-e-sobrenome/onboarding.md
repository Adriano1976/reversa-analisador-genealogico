# Onboarding: testar a busca por nome e sobrenome

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Para: quem vai testar esta feature pela primeira vez, à mão, no navegador.

## 1. Pré-requisitos

- O interpretador **oficial** do projeto é o `.venv/` (`requirements.txt`, topo do arquivo). Todos os
  comandos abaixo usam `.venv\Scripts\python.exe`.
- Uma árvore GEDCOM **sintética** e um relatório de matches **sintético**. Dado real de terceiros não
  entra no repositório nem na pasta de teste (princípio I).
- Nenhuma dependência nova é necessária para esta feature.

## 2. Subir a aplicação

**Caminho A — sem entrada pelo Google (é o caminho para testar esta feature).** Depois da feature 051,
o `__main__` recusa subir sem as cinco variáveis de ambiente
(`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `ANALISADOR_SECRET_KEY`, `ANALISADOR_URL_PUBLICA`,
`ANALISADOR_DONO_INICIAL`). Para testar a busca sem montar OAuth, suba pela fábrica, que é o mesmo
caminho da suíte e do invólucro de paridade:

```
cd src
..\.venv\Scripts\python.exe -c "from app import create_app; create_app().run(host='127.0.0.1', port=5000)"
```

Nesse caminho a aplicação roda sem sessão, com o dono legado `"unico"` e a pasta plana — o
comportamento descrito no `addenda/051`.

**Caminho B — com entrada real.** Defina as cinco variáveis e suba pelo `__main__`. A busca é idêntica;
a diferença é que a resposta passa a ser escopada pela conta.

## 3. Roteiro executável

Execute na ordem. Cada passo diz o que deve aparecer.

1. **Abra `http://127.0.0.1:5000/`.** A tela mostra as fases 1, 2 e 3.
   *Esperado:* **não** há campo de busca ainda — não há árvore aberta.
2. **Fase 1 — envie ou escolha uma árvore.** Abra a árvore.
   *Esperado:* as fases 2 e 3 deixam de pedir árvore, e o **campo de busca aparece no cabeçalho**.
3. **Busque um sobrenome** (`Silva`).
   *Esperado:* a seção **árvore** lista acertos com nome, nascimento, falecimento, pais e
   identificador; o rodapé declara o total quando passa de 50.
4. **Busque um nome completo** com caixa e acento trocados (`jose DA silva`).
   *Esperado:* o mesmo conjunto do passo anterior para aquele nome — acento e caixa não mudam nada.
5. **Busque um trecho no meio do token** (`ilva`).
   *Esperado:* os mesmos `Silva` do passo 3, e os que começam por `Sil` aparecem **antes** dos que
   apenas contêm o trecho.
6. **Repita a busca do passo 3 uma segunda vez.**
   *Esperado:* a **mesma ordem**, item por item.
7. **Busque um termo que não existe** (`Zzzz`).
   *Esperado:* a tela diz que não encontrou, o campo **mantém o texto digitado** e nada é gravado.
8. **Fase 3 — selecione um relatório de matches e busque um nome que existe nele.**
   *Esperado:* a seção **relatório** aparece com o nome do arquivo de origem, o kit e o cM; se o nome
   também existe na árvore, aparece o caminho para a ficha.
9. **Selecione um arquivo que não é relatório de matches e busque.**
   *Esperado:* a seção do relatório **não aparece**, a tela diz que ele não pôde ser lido, e a seção
   da árvore continua respondendo normalmente.
10. **Com árvore aberta, rode uma análise de DNA e anote o veredito; faça buscas; repita a análise.**
    *Esperado:* veredito, contagem de conexões e descartados **idênticos**.

## 4. O que observar com atenção

- **O campo de busca não pode se comportar como o combobox.** Ele precisa estar **visível** sem que o
  operador saiba que existe, e o resultado precisa ser lido ao entrar na tela — não escondido atrás de
  uma tecla.
- **A seção da árvore e a do relatório não se misturam.** São duas perguntas diferentes e precisam
  aparecer rotuladas.
- **`não encontrei` nunca pode aparecer como "erro".** E "relatório ilegível" nunca pode parecer
  "nada encontrado".
- **O combobox dos três campos de nome tem de continuar funcionando exatamente como antes.** Ele não é
  tocado nesta entrega.

## 5. Verificação automatizada

```
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tests\rodar_paridade.py
```

- **Suíte:** o marco de partida é **1.745 passam / 9 pulados / 4 falham**, e as 4 falhas são
  pré-existentes (`addenda/051`). A entrega acrescenta testes; nenhum teste existente é ajustado.
- **Paridade:** sem divergência nova contra a linha de base.

## 6. Checklist manual (o que nenhum teste prende)

A busca é servida pelo servidor, então quase tudo é verificável por `pytest`. Fica manual:

- [ ] O campo aparece no lugar esperado do cabeçalho, no desktop e na janela estreita.
- [ ] O resultado é anunciado por leitor de tela (região viva) e o foco é visível.
- [ ] O botão de buscar é operável por teclado (Enter no campo submete).
- [ ] A página com árvore aberta continua carregando em tempo aceitável.

## 7. Se algo der errado

| Sintoma | Onde olhar |
|---------|-----------|
| A busca devolve nomes de outra árvore | Índice pendurado no grafo? O cenário reproduzível é o de **duas árvores do mesmo tamanho** (`data-delta.md#3`) |
| A ordem muda entre duas buscas iguais | Chave total do ranking — `(-pontuacao, nome_normalizado, xref)` (`roadmap.md#D-05`) |
| O veredito da análise mudou depois da entrega | Um normalizador foi unificado por engano — `RN-06` proíbe |
| `SHA_DA_TELA` falhou | O bloco de busca vazou para a tela vazia; ele só pode existir sob `{% if gedcom_filename %}` |
