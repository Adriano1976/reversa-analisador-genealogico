"""Varredura do escape ANTES do CHG-001 do BUG-20260929-J6PQ.

Prova a causacao do BUG-20261002-T4ZM: os 14 caracteres descartados hoje eram
preservados antes da troca de lista negra por lista branca.

A funcao abaixo foi extraida VERBATIM de
`c709ea0^:analisador-genealogico/reconstructed/path_search.py`, ou seja, do
commit imediatamente anterior ao que aplicou a correcao do J6PQ. Nao foi
reescrita: e o corpo original, copiado.

Saida no mesmo formato tabulado da sonda do candidato, para comparacao direta.
"""
import re
import unicodedata


def _mermaid_label_pre_correcao(txt) -> str:
    """Rotulo de no Mermaid: NFC, sem controle, com &, < e > escapados."""
    s = unicodedata.normalize("NFC", str(txt))
    s = (s.replace('\u00A0', ' ')
           .replace('\u2013', '-')
           .replace('\u2014', '-')
           .replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'"))
    s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    s = s.replace('"', "'")
    return re.sub(r'[\r\n]+', ' ', s)


print("lado: pre-correcao")
print("origem: c709ea0^:analisador-genealogico/reconstructed/path_search.py")
print()
for codigo in range(0x20, 0x7F):
    ch = chr(codigo)
    payload = "Ana%sSilva" % ch
    linha = 'N_I1["%s"]' % _mermaid_label_pre_correcao(payload)
    rotulo = linha.split('["', 1)[1].rsplit('"]', 1)[0]
    print("%02X\t%r\t%s" % (codigo, ch, rotulo))
