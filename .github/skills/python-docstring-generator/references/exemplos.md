# Exemplos adicionais — Google Style Guide

Use estes exemplos como referência de formatação para casos além da função simples já mostrada no `SKILL.md`.

## Classe

```python
class GerenciadorDeCache:
    """Gerencia o armazenamento temporário de resultados de consultas.

    Attributes:
        capacidade (int): Número máximo de itens armazenados simultaneamente.
        ttl_segundos (int): Tempo de vida de cada item em segundos.
    """

    def __init__(self, capacidade: int = 100, ttl_segundos: int = 60) -> None:
        """Inicializa o gerenciador de cache com a capacidade e o TTL informados.

        Args:
            capacidade (int): Número máximo de itens armazenados simultaneamente. Padrão é 100.
            ttl_segundos (int): Tempo de vida de cada item em segundos. Padrão é 60.
        """
        self.capacidade = capacidade
        self.ttl_segundos = ttl_segundos
        self._dados = {}

    def obter(self, chave: str) -> Optional[str]:
        """Recupera um valor armazenado no cache pela chave.

        Args:
            chave (str): A chave do item a ser recuperado.

        Returns:
            Optional[str]: O valor armazenado, ou None se a chave não existir.
        """
        return self._dados.get(chave)
```

## Módulo

```python
"""Utilitários para validação e formatação de CPF e CNPJ brasileiros.

Este módulo expõe as funções `validar_cpf`, `validar_cnpj` e
`formatar_documento`, usadas para checar e exibir documentos fiscais
no padrão da Receita Federal.
"""

import re


def validar_cpf(cpf: str) -> bool:
    """Valida um número de CPF conforme o algoritmo de dígitos verificadores.

    Args:
        cpf (str): O CPF a ser validado, com ou sem pontuação.

    Returns:
        bool: True se o CPF for válido, False caso contrário.
    """
    ...
```

## Função sem argumentos e sem retorno relevante

Quando não há parâmetros nem valor de retorno relevante, o docstring é apenas a descrição curta — sem `Args:` nem `Returns:`.

```python
def limpar_cache() -> None:
    """Remove todos os itens armazenados no cache em memória."""
    _cache.clear()
```

## Função geradora (usa `yield`)

```python
def ler_linhas(caminho: str) -> Iterator[str]:
    """Lê um arquivo de texto e produz uma linha por vez.

    Args:
        caminho (str): Caminho do arquivo a ser lido.

    Yields:
        str: A próxima linha do arquivo, sem o caractere de quebra de linha.
    """
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            yield linha.rstrip("\n")
```
