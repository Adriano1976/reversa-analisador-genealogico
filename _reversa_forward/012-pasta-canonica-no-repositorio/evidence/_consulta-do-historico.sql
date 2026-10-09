-- Consulta ao historico da feature 008, feita na feature 012 (2026-10-09).
--
-- Por que isto importa: o expurgo do residuo (RF-10) remove 18 arquivos de src/uploads.
-- As colunas tree_ref e match_file_ref de `dna_analysis` guardam o NOME do arquivo
-- armazenado. Se alguma linha do historico apontar para um nome que o expurgo remove,
-- o expurgo cria referencia quebrada -- e isso nao esta medido em nenhum artefato.
-- Se nao houver histórico nenhum, o expurgo nao tem o que quebrar, e isso fica provado.

\pset pager off
\echo '== tabelas do schema public =='
select table_name from information_schema.tables
 where table_schema = 'public' order by 1;

\echo '== quantas analises registradas =='
select count(*) as analises from dna_analysis;

\echo '== tree_ref distintas =='
select distinct tree_ref from dna_analysis order by 1;

\echo '== match_file_ref distintas =='
select distinct match_file_ref from dna_analysis order by 1;

\echo '== quando foram registradas =='
select min(created_at) as primeira, max(created_at) as ultima from dna_analysis;
