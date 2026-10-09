# Conferencia de escopo por diff - T020 (D-08)
# Gerado em (UTC): 2026-10-09T14:57:31Z
# Comandos: git status --short -- src _reversa_sdd ; git diff --stat -- src _reversa_sdd

## git status --short -- src _reversa_sdd

?? _reversa_sdd/parity/_collect_cand.py
?? _reversa_sdd/parity/_collect_oracle.py

## git diff --stat -- src _reversa_sdd

(vazio: NENHUM arquivo rastreado de src/ ou _reversa_sdd/ foi modificado)

## sha256 do instrumento de paridade

33E45B055AEF845872530A7631A2565E2B8DC3E82DF536C8AB787FDF4FE14D37

## Arquivos tocados por esta feature

 M README.md
 M docker-compose.yml
?? tests/manutencao_de_uploads.py
?? tests/rodar_paridade.py
?? tests/test_documentacao_do_upload.py
?? tests/test_manutencao_de_uploads.py
?? tests/test_rodar_paridade.py

## Leitura

Os dois unicos arquivos nao rastreados sob _reversa_sdd/ sao _collect_cand.py e
_collect_oracle.py: copias GERADAS pelo harness a cada execucao, que o proprio
_clean_residue.py declara como residuo. Nao sao alteracao de fonte.
O harness.py conserva o mesmo sha256: o instrumento nao foi editado (D-07).

