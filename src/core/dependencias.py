"""O que o nucleo consome de fora, entregue pela borda.

A classe morava em `core/dna_analysis.py` e e consumida por `core/path_search.py`
e por `src/app.py`. Saiu para ter endereco proprio: um contrato de tres
consumidores nao deve morar dentro de um arquivo que muda por outro motivo.
"""
from __future__ import annotations




class Dependencias:
    """O que a analise de DNA consome de FORA do nucleo (RF-09, `T016`).

    A leitura do CSV e a emissao do diagrama sao borda, e a borda as entrega. O
    nucleo chama as funcoes, sem importar `parsers/csv_ingest` nem
    `reporting/mermaid_render` — que e o que a guarda de dependencias cobra.

    A classe existe porque sao QUATRO dependencias relacionadas, e quatro
    parametros soltos na assinatura de `dna_analysis` convidariam a trocar a
    ordem por engano. Ela nao guarda estado de dominio: so carrega as funcoes.
    """

    __slots__ = ("read_csv", "detect_columns", "aggregate_matches", "generate_mermaid",
                 "generate_mermaid_indirect", "anotar_profundidade",
                 "gerar_mermaid_da_sugestao")

    def __init__(self, read_csv, detect_columns, aggregate_matches, generate_mermaid,
                 generate_mermaid_indirect=None, anotar_profundidade=None,
                 gerar_mermaid_da_sugestao=None):
        self.read_csv = read_csv
        self.detect_columns = detect_columns
        self.aggregate_matches = aggregate_matches
        self.generate_mermaid = generate_mermaid
        self.generate_mermaid_indirect = generate_mermaid_indirect
        # Opcional de proposito: e a unica dependencia que so acrescenta DESENHO ao
        # diagrama ja pronto, e sem ela o fluxo continua inteiro. Ver
        # `reporting.mermaid_render.anotar_profundidade`.
        self.anotar_profundidade = anotar_profundidade
        # Opcional pelo mesmo motivo (feature 032): sem ela o cartao mostra o resumo da
        # arvore sugerida e nao o desenho. `core/` nao pode importar `reporting/`
        # (ADR-34), entao o emissor entra pela borda.
        self.gerar_mermaid_da_sugestao = gerar_mermaid_da_sugestao
