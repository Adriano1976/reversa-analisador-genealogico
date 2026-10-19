"""Sonda descartavel: quantos cartoes da analise real tem arvore sugerida.

Nao e teste nem entrega. Mede, no par de arquivos REAL escolhido, a distribuicao
de vereditos (028) e de sugestoes (029/032) para responder uma pergunta de
produto: a arvore sugerida pode aumentar a contagem de "com caminho"?

Imprime apenas AGREGADOS e booleanos; nomes de pessoas nao vao para a saida.
"""
import sys
from collections import Counter

sys.path.insert(0, "src")

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import (  # noqa: E402
    aggregate_matches,
    detect_columns,
    read_csv_with_fallback,
)
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
    mermaid_da_sugestao,
)

GEDCOM = sys.argv[1]
CSV = sys.argv[2]
RAIZ = sys.argv[3]

deps = Dependencias(
    read_csv_with_fallback,
    detect_columns,
    aggregate_matches,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
    anotar_profundidade,
    mermaid_da_sugestao,
)

arvore = carregar_arvore(GEDCOM)
results, skipped, msg = dna_analysis(CSV, RAIZ, deps, arvore)

com_caminho = [r for r in results if r["documentary"] and r["documentary"].get("path")]
sugeridos = [r for r in results if (r.get("sugestao_geracoes") or 0) >= 1]

print("cartoes:", len(results))
print("com_caminho:", len(com_caminho))
print("ambiguos:", sum(1 for r in results if r["documentary"] and r["documentary"].get("ambiguous_identity")))
print("vereditos:", dict(Counter(r.get("validacao_status") for r in results)))
print("com_sugestao:", len(sugeridos))
print("geracoes_sugeridas:", dict(Counter(r.get("sugestao_geracoes") for r in sugeridos)))

# Os cartoes em conflito que NAO conseguiram sugestao: e' aqui que mora a perda.
em_conflito = [r for r in results if r.get("validacao_status") != "VALIDADO" and r.get("validacao_status") != "INCONCLUSIVO"]
print("em_conflito:", len(em_conflito))
print("conflito_sem_sugestao:", sum(1 for r in em_conflito if (r.get("sugestao_geracoes") or 0) < 1))
print("conflito_sem_caminho:", sum(1 for r in em_conflito if not (r["documentary"] and r["documentary"].get("path"))))

# Descartados: nomes do CSV que nao viraram cartao nenhum.
print("descartados:", len(skipped))
print("motivos:", dict(Counter((s.get("motivo") or "?").split(" (")[0] for s in skipped)))
print("alvo_nos_descartados:", any(
    "manoel" in (s.get("csv_name") or "").lower()
    and "vieira" in (s.get("csv_name") or "").lower() for s in skipped))

print("com_desenho:", sum(1 for r in results if r.get("sugestao_mermaid")))
# O caso que a tela esconde: o cartao conta como "sem caminho" (o parentesco foi
# trocado pela janela de vida) mas a cirurgia usa o documento ORIGINAL e desenha.
print("desenho_sem_caminho_contado:", sum(
    1 for r in results
    if r.get("sugestao_mermaid") and not (r["documentary"] and r["documentary"].get("path"))))
print("geracoes_sugeridas_mesmo_sem_desenho:",
      sum(1 for r in results if (r.get("sugestao_geracoes") or 0) >= 1
          and not r.get("sugestao_mermaid")))

# O titulo do cartao e' `match_name` (nome na arvore), nao o nome do CSV: os dois
# divergem quando a identidade foi casada com grafia diferente.
def _tem(r, campo, a, b):
    nome = (r.get(campo) or "").lower()
    return a in nome and b in nome


alvo = [r for r in results if _tem(r, "match_name", "manoel", "vieira")
        or _tem(r, "csv_name", "manoel", "vieira")]
print("alvo_encontrado:", bool(alvo))
for r in alvo[:1]:
    documental = r["documentary"] or {}
    degrees = documental.get("degrees") or {}
    print("  status:", r.get("validacao_status"))
    print("  tem_caminho:", bool(documental.get("path")))
    print("  a_up:", degrees.get("a_up"), "b_up:", degrees.get("b_up"))
    print("  cm:", r.get("cm"), "geracoes_do_kit:", r.get("geracoes_do_kit"))
    print("  sugestao_geracoes:", r.get("sugestao_geracoes"))
    print("  resumo:", r.get("sugestao_resumo"))
    print("  tem_desenho:", bool(r.get("sugestao_mermaid")))

# A forma dos cartoes COM caminho: so' numeros, sem nomes.
print("--- cartoes com caminho (cm/a_up/kit/status/sugestao) ---")
for r in com_caminho:
    degrees = (r["documentary"] or {}).get("degrees") or {}
    print(" ", r.get("cm"), degrees.get("a_up"), degrees.get("b_up"),
          r.get("geracoes_do_kit"), r.get("validacao_status"), r.get("sugestao_geracoes"))
