"""Reconhecimento: que marcas de VIDA e de PRIVACIDADE este GEDCOM tem?

Antes de contar "pessoas vivas" e' preciso saber o que o arquivo oferece para responder isso.
Num GEDCOM, "viva" costuma ser inferido por AUSENCIA de obito, mas ha' outras marcas possiveis:

  - ausencia de `DEAT`;
  - `DEAT Y` (obito declarado sem data);
  - `RESN privacy` / `RESN locked` (restricao de privacidade);
  - nome VAZIO ou substituido ("Indivíduo", "Living", "Privado") — a forma mais comum de
    anonimizar quem esta' vivo;
  - tags proprietarias (`_LIVING`, `_PRIVATE`).

Este script conta o vocabulario de tags de nivel 1 e cruza os sinais, sem concluir nada ainda.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\vivos_reconhecimento.py
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(R, "src", "uploads",
                   "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")


def main():
    arvore = carregar_arvore(GED)
    pessoas = arvore[0]
    print(f"pessoas: {len(pessoas)}")

    tags = collections.Counter()
    for pessoa in pessoas.values():
        for r in pessoa.sub_records:
            tags[r.tag] += 1
    print("\n" + "=" * 90)
    print("TAGS DE NIVEL 1, POR FREQUENCIA (as 30 primeiras)")
    print("=" * 90)
    for tag, quantidade in tags.most_common(30):
        print(f"  {tag:<16} {quantidade:>7,}".replace(",", "."))

    suspeitas = [t for t in tags if "LIV" in t.upper() or "PRIV" in t.upper()
                 or "RESN" in t.upper() or t.upper().startswith("_")]
    print(f"\n  tags que podem marcar vida/privacidade: {suspeitas}")

    # `DEAT` presente? com que valor?
    com_deat = 0
    deat_y = 0
    valores_deat = collections.Counter()
    for pessoa in pessoas.values():
        achou = False
        for r in pessoa.sub_records:
            if r.tag == "DEAT":
                achou = True
                valores_deat[str(r.value).strip()[:12]] += 1
        if achou:
            com_deat += 1
            if str(pessoas[id(pessoa)] if False else "").strip() == "":
                pass
    print(f"\n  registros com DEAT ............. {com_deat:,}".replace(",", "."))
    print(f"  registros sem DEAT ............. {len(pessoas) - com_deat:,}".replace(",", "."))
    print(f"  valores de DEAT mais comuns: {valores_deat.most_common(6)}")

    # Nome vazio ou generico?
    vazios, genericos = 0, collections.Counter()
    for pessoa in pessoas.values():
        nome = (get_name(pessoa) or "").strip()
        if not nome:
            vazios += 1
            continue
        limpo = nome.split("[")[0].strip()
        if limpo.lower() in ("indivíduo", "individuo", "living", "privado", "private", "?"):
            genericos[limpo] += 1
    print(f"\n  registros com nome VAZIO ........ {vazios:,}".replace(",", "."))
    print(f"  registros com nome GENERICO ..... {sum(genericos.values()):,}".replace(",", "."))
    print(f"    {dict(genericos)}")


if __name__ == "__main__":
    main()
