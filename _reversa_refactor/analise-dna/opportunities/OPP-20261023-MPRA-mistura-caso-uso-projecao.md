---
schema_version: 1
id: OPP-20261023-MPRA
display_number: 35
context: analise-dna
verb: modularize
title: Caso de uso e projeção de porta misturados no mesmo módulo
target:
  files: [src/application/dna_analysis.py]
  symbol: projetar_analise, _juntar, _ficha, _papeis_do_caminho, _kits, _pessoas, _conexao
smell: >
  Um módulo de application/ carrega duas responsabilidades disjuntas: (1) o caso de uso
  orquestrador dna_analysis, que chama o nucleo e persiste, e (2) a projeção pura do resultado
  para o payload da porta (projetar_analise + 6 auxiliares privados). A projeção não tem efeito
  e não depende do caso de uso; o caso de uso só precisa chamar projetar_analise. São dois papéis
  que crescem por razões diferentes.
roi:
  confidence: green
  impact: >
    A separação isola a única parte testável sem banco (a projeção) em módulo próprio, reduz o
    tamanho do caso de uso para ~55 linhas e permite exercitar o mapper sem nenhuma dependência de
    infraestrutura. A docstring do próprio arquivo já declara a projeção como "pura" e "publica
    para poder ser exercitada sem banco" (B003), reforçando que ela pede fronteira própria.
  cost: low
  est_return: >
    dna_analysis.py reduzido a ~55 linhas (só o caso de uso), projecao_analise.py novo com ~235
    linhas coesas. Testes de projeção desacoplados de infraestrutura. Alta coesão por módulo.
state: applied
traceability:
  soul: []
  specs:
    - _reversa_sdd/analise-dna/design.md
    - _reversa_sdd/analise-dna/requirements.md#RF-20
    - _reversa_sdd/adrs/25-fronteira-de-aplicacao-portas.md
    - _reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md
---

## Antes observado

`src/application/dna_analysis.py` tem 346 linhas e dois papéis:

**Papel 1 — Caso de uso orquestrador** (~55 linhas úteis):
- `ResultadoDeAnalise` (dataclass de saída, linhas 42-70)
- `dna_analysis` (linha 292-342): chama `fluxo_dna`, coleta observações/cobertura, chama o
  registro se disponível, monta e devolve `ResultadoDeAnalise`

**Papel 2 — Mapper/Projetor para a porta** (~235 linhas):
- `_juntar` (79-94): merge de pessoa no retrato por xref
- `_ficha` (97-110): converte `person_summary` em `PessoaDaAnalise`
- `_papeis_do_caminho` (113-139): extrai pares `(xref, papel)` do caminho documental
- `_kits` (142-174): constrói `tuple[KitDaAnalise, ...]` por índice
- `_pessoas` (177-202): retrato de todas as pessoas e resolução da raiz
- `_conexao` (205-232): constrói `ConexaoDaAnalise` de um resultado individual
- `projetar_analise` (235-289): orquestra os anteriores e devolve `AnaliseParaRegistrar`

A própria docstring do módulo (linha 22-24) declara: *"A projeção do resultado para o payload
da porta vive **aqui**, e é **pura**: ela lê o que o núcleo devolveu e nada mais"*. E o
comentário da linha 75 diz: *"Pública para poder ser exercitada sem banco: ela é pura, e o teste
dela não precisa de `DATABASE_URL`"*. O arquivo já sabe que a projeção é separável.

## Transformação proposta

Extrair as linhas 73-289 para `src/application/projecao_analise.py`, mantendo o `__all__`
adequado nos dois módulos. O `dna_analysis.py` passaria a importar apenas `projetar_analise` de
`projecao_analise`.

```
src/application/
  dna_analysis.py          # ~55 linhas: ResultadoDeAnalise + dna_analysis
  projecao_analise.py      # ~235 linhas: os 6 auxiliares + projetar_analise (NOVO)
```

## Fronteira de comportamento

A separação é **puramente estrutural**: nenhuma linha de lógica muda, apenas o arquivo onde vive.
O comportamento externo, os testes e a porta `RegistroDeAnalises` permanecem idênticos.

## Rede de segurança

A suíte existente cobre o comportamento de produção. A projeção já é pura e sem efeito, então a
separação não exige nova caracterização — o gate é a suíte verde antes e depois.

---
*Gerado pelo Reversa-Refactor em 2026-10-23.*
