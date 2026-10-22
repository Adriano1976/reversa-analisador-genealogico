# Roadmap: Renomear o filtro de segmentos no título do bloco

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Modo: express

## 1. Resumo da abordagem

Trocar um literal do template por um título que nomeia o filtro, com o limite vindo do payload
(`result.endogamia.limiares.segmento`) para não existir um segundo `10` no projeto. O teste que prendia
o literal antigo passa a prender o novo. Nenhuma regra, número, selo ou rótulo estrutural é tocado.

## 5. Delta arquitetural

| Componente | Tipo | Arquivo alvo |
|---|---|---|
| `templates/index.html` | contrato-alterado | `src/templates/index.html` (título do bloco `endogamia-bloco`) |
| `tests` | contrato-alterado | `tests/test_endogamia.py` (literal preso no teste de "sem fato nenhum") |
