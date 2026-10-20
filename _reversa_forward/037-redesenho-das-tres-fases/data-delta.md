# Delta de dados: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Base extraída: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`

## 1. Veredito

**Nenhum delta de dado.** A feature não cria, remove nem altera campo, tabela, payload, chave, índice ou migração. O banco PostgreSQL opcional continua com as seis tabelas extraídas, e o formato dos arquivos em disco não muda.

## 2. Entidades verificadas

| Entidade | Onde | Tocada? | Por quê |
|---|---|---|---|
| `ItemDaLista` | `src/reporting/lista_de_arquivos.py` (dataclass congelada, em memória) | não | A tela passa a **ler** `disponivel` também para contar; nenhum campo nasce |
| `EntradaArmazenada` | `src/ports/adaptadores.py` (valor de retorno de `listar`) | não | A listagem continua perguntando o mesmo à porta |
| `analysis`, `analysis_person`, `match_result`, `match_path_node`, `analysis_file`, `schema_version` | `docker/init.sql` | não | Nenhuma coluna, `FOREIGN KEY` ou `CHECK` é tocada |
| Arquivos em `src/uploads/` e `src/uploads/_aposentados/` | disco | não | Nenhum nome, sufixo ou convenção muda |
| `all_names` | variável de template (`list[str]`) | **representação**, não dado | Continua a mesma lista, na mesma ordem, vinda do mesmo lugar; muda só como é escrita no documento |

## 3. O que muda, e não é dado

`all_names` deixa de virar um `<option>` por nome e passa a ser escrita **uma vez** como JSON:

```html
<script type="application/json" id="nomes-da-arvore">["Ana Silva Souza", "Carlos Silva Souza", ...]</script>
```

Três observações:

1. **O conteúdo é o mesmo.** Mesma lista, mesma ordem, mesma origem (`resultado.nomes`, do caso de uso de upload, e `all_names` de `selecionar_arvore`).
2. **O consumidor muda.** Antes, o navegador lia a `<datalist>`; agora o script lê o JSON.
3. **A barreira de segurança é a mesma.** O filtro `tojson` escapa `<`, `>` e `&`; nome com `</script>` sai como sequência unicode e não fecha a tag. Há teste para isso.

## 4. Migração

n/a — não há nada a migrar. Não existe estado persistido que represente a tela: a reorganização vale a partir do primeiro carregamento.

## 5. Como verificar que o delta é zero

- `_reversa_sdd/erd-complete.md` não é citado por nenhum arquivo alterado — conferir `git diff --stat`.
- Nenhum arquivo de `src/application/`, `src/ports/`, `src/core/` aparece no diff.
- `docker/init.sql` e `requirements.txt` inalterados.
- O contrato de `GET /app.css` e das duas rotas de arte continua idêntico.
