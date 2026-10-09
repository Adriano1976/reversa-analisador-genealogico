# Isolamento do instrumento - T017
# Gerado em (UTC): 2026-10-09T14:54:12Z
# Comando: .venv\Scripts\python.exe tests\rodar_paridade.py  (o involucro, D-07)
# exit code: 0
# pasta real (src\uploads): 36 -> 36 arquivos
# pasta real alterada? NAO - inventario identico
# CONTROLE POSITIVO - arquivos criados na pasta descartavel: 13

pasta de upload isolada: D:\Projetos\reversa_analisador_gelealogico\.parity-tmp\uploads
==============================================================================
HARNESS DIFERENCIAL � oraculo congelado x reconstrucao
==============================================================================
oraculo   : _reversa_sdd\oracle\app_legacy_e43ca22.py
candidato : src/
probes    : 40 valores de cM + grafo completo + pares de caminho + decomposicao + analise de DNA pela rota
amostra   : 40x40 = 1600 pares de caminho por lado
timeout   : 600s por coletor

------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\affinity.ged (417 bytes)
  ORACLE coletado: 6 pessoas, 3 familias
  CANDIDATO coletado: 6 pessoas, 3 familias
  PARIDADE OK � zero divergencia
------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\basic.ged (523 bytes)
  ORACLE coletado: 7 pessoas, 2 familias
  CANDIDATO coletado: 7 pessoas, 2 familias
  PARIDADE OK � zero divergencia
------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\deep25.ged (2439 bytes)
  ORACLE coletado: 25 pessoas, 24 familias
  CANDIDATO coletado: 25 pessoas, 24 familias
  PARIDADE OK � zero divergencia
------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\mojibake_latin1.ged (257 bytes)
  ORACLE coletado: 3 pessoas, 1 familias
  CANDIDATO coletado: 3 pessoas, 1 familias
  PARIDADE OK � zero divergencia
------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\no_name.ged (233 bytes)
  ORACLE coletado: 3 pessoas, 1 familias
  CANDIDATO coletado: 3 pessoas, 1 familias
  PARIDADE OK � zero divergencia
------------------------------------------------------------------------------
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\variants.ged (507 bytes)
  ORACLE coletado: 6 pessoas, 2 familias
  CANDIDATO coletado: 6 pessoas, 2 familias
  PARIDADE OK � zero divergencia

==============================================================================
RESULTADO: PARIDADE 100%% (zero divergencia)
==============================================================================

--- comparacao antes/depois da pasta real ---
(vazio: nenhuma diferenca)

--- arquivos na pasta descartavel ---
19da3bae17746752__no_intersection.csv
202881c5bff9b799__generic.csv
2fb588e6670bc166__probe.ged
3835dd799786d4ee__probe.ged
513e3f04c229d32f__probe.ged
641b786ce546bff6__cm_boundaries.csv
72f459ae1591d177__latin1.csv
739b8f1005995e08__utf8.csv
78dc213cb27fdd2d__probe.ged
8ccc014af6ea76e0__duplicated.csv
996082fbcceb908e__probe.ged
a36c0d2aae577481__missing_col.csv
cf5b3295b82210e8__probe.ged
