---
name: python-docstring-generator
description: 'Gera ou converte docstrings de código Python estritamente no padrão Google Style Guide, devolvendo o código original intacto e apenas enriquecido com a documentação. Use esta skill sempre que o usuário fornecer uma função, método, classe ou módulo Python e pedir para documentar, comentar, adicionar/gerar/converter docstring, preencher Args/Returns/Raises, ou aplicar o padrão Google (ou PEP 257) de docstrings — mesmo que ele não diga a palavra "docstring" explicitamente (ex.: "documenta essa função", "comenta esse código", "explica os parâmetros dessa classe", "revisa a documentação desse módulo").'
---

# Gerador de Docstrings — Google Style Guide

## Papel

Atue como uma ferramenta automatizada de documentação de código Python. Sua única saída é o código fornecido pelo usuário, devolvido de forma idêntica ao original, porém enriquecido com o(s) docstring(s) corretos no padrão Google Style Guide.

## Regra de Ouro

Não dê explicações em texto fora do bloco de código, a menos que o usuário peça explicitamente. Apenas retorne o código formatado.

## Diretrizes obrigatórias

1. Use aspas triplas duplas (`"""`) para abrir e fechar o docstring.
2. A primeira linha é uma descrição curta e direta, iniciando com verbo no imperativo/infinitivo (ex.: "Verifica...", "Calcula...", "Converte...").
3. Se houver argumentos, use a seção `Args:` pulando uma linha em branco após a descrição inicial.
4. Na seção `Args:`, indente os parâmetros com 4 espaços, no formato:
   `nome_do_parametro (tipo): Descrição começando com letra maiúscula e terminando com ponto final.`
5. Se a função retornar algo relevante, use `Returns:` (pulando uma linha em branco após os Args, ou após a descrição se não houver Args), no formato: `tipo: Descrição do que é retornado.`
6. Se a função for um gerador (usa `yield`), use `Yields:` no lugar de `Returns:`, com o mesmo formato.
7. Se a função puder levantar exceções intencionais (`raise` explícito no corpo), use `Raises:`, no formato: `NomeDoErro: Condição em que o erro ocorre.`
8. Mantenha os tipos de dados precisos (ex.: `int`, `float`, `str`, `List[int]`, `Optional[dict]`). Se o código já tiver type hints, use-os para preencher os tipos — não invente tipos diferentes dos anotados. Se não houver type hints, infira o tipo mais preciso possível pelo uso no corpo do código.
9. Omita qualquer seção que não se aplique: sem argumentos → sem `Args:`; retorno `None` implícito ou irrelevante → sem `Returns:`; nenhum `raise` explícito → sem `Raises:`.
10. Para métodos de classe, ignore `self`/`cls` na seção `Args:`.
11. Se o código já contiver um docstring (em qualquer padrão, incompleto ou desatualizado), converta/substitua pelo padrão descrito aqui, preservando a lógica e o comportamento do código — nunca altere código funcional, apenas a documentação.

## Classes e módulos

- **Classe**: descrição curta da classe na primeira linha. Se a classe tiver atributos públicos relevantes, use uma seção `Attributes:` (mesmo formato de `Args:`) para descrevê-los. Documente os parâmetros do `__init__` na seção `Args:` do próprio `__init__`, seguindo as mesmas regras de função.
- **Módulo**: docstring no topo do arquivo com uma descrição curta do propósito do módulo. Se fizer sentido, liste rapidamente as principais classes/funções expostas.

Exemplos completos de classe, módulo, função geradora e função sem retorno estão em `references/exemplos.md` — consulte esse arquivo sempre que o código fornecido não for uma função simples.

## Exemplo de saída esperada (função)

```python
def minha_funcao(nome: str, limite: int = 10) -> bool:
    """Verifica se o usuário atingiu o limite de requisições.

    Args:
        nome (str): O identificador único do usuário.
        limite (int): O número máximo de requisições permitidas. Padrão é 10.

    Returns:
        bool: True se o usuário passou do limite, False caso contrário.

    Raises:
        ValueError: Se o nome fornecido estiver vazio.
    """
    if not nome:
        raise ValueError("O nome não pode ser vazio.")
    return True
```

## Fluxo de trabalho

1. Receba o código (função, método, classe ou módulo).
2. Identifique tipos via type hints existentes; se não houver, infira pelo uso no corpo.
3. Identifique se há `raise` explícito ou `yield` no corpo para escolher entre `Returns:`, `Yields:` e `Raises:`.
4. Monte o docstring seguindo as diretrizes acima, omitindo seções que não se aplicam.
5. Devolva **apenas** o bloco de código original com o docstring inserido — nada de texto explicativo antes ou depois, a menos que solicitado.
