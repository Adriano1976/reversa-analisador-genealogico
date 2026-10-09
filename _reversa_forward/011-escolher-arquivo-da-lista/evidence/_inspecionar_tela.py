"""Inspeciona o HTML servido pelo app: a lista e apenas exibida, ou tambem ESCOLHIVEL?"""
import urllib.request

h = urllib.request.urlopen("http://127.0.0.1:5000/").read().decode("utf-8")

i = h.find("Backup-Arvore-Sandro")
print("--- trecho em volta do primeiro item da lista de arvores ---")
print(h[max(0, i - 520):i + 220])
print()
print("--- elementos de ESCOLHA presentes na tela ---")
marcas = [
    ('name="gedcom_filename"', "campo oculto gedcom_filename"),
    ("<select", "elemento select"),
    ('type="radio"', "radio"),
    ('type="submit"', "botao de submit"),
    ("list-group-item-action", "item clicavel (classe Bootstrap)"),
    ("<a href", "link"),
]
for marca, rotulo in marcas:
    print("  {:<34} {}".format(rotulo, marca in h))
