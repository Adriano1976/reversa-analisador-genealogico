#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gedcom_process.py - Desambiguação de homônimos, expansão de locais, validação
biológica e injeção de status de vida (_ALIV / RESN) em arquivos GEDCOM (.ged).

Uso típico:
  python gedcom_process.py arvore.ged --dry-run                  # só diagnóstico
  python gedcom_process.py arvore.ged -o saida.ged --lineage "Linhagem de Sergipe" \
         --ref-person "Celso Gomes Gama" --fix-ages

Somente biblioteca padrão. Preserva codificação, BOM, finais de linha e linhas
não tocadas (byte a byte quando possível).
"""
import argparse, codecs, collections, json, re, sys, unicodedata
from pathlib import Path

LINE_RE = re.compile(r'^(\s*)(\d+)\s+(?:(@[^@\s]+@)\s+)?(\S+)(?:\s(.*))?$')
NAME_RE = re.compile(r'^([^/]*)/([^/]*)/?(.*)$')
YEAR_RE = re.compile(r'(?<!\d)(\d{4})(?!\d)')


# ----------------------------------------------------------------- modelo ---
class Line:
    def __init__(self, level, xref, tag, value, indent='', raw=None):
        self.level, self.xref, self.tag, self.value = level, xref, tag, value
        self.indent, self.raw = indent, raw

    def set_value(self, v):
        self.value, self.raw = v, None

    def text(self):
        if self.raw is not None:
            return self.raw
        s = ' '.join([str(self.level)] + ([self.xref] if self.xref else []) + [self.tag])
        if self.value not in (None, ''):
            s += ' ' + self.value
        return self.indent + s


class Record:
    def __init__(self):
        self.lines = []

    @property
    def xref(self):
        return self.lines[0].xref

    @property
    def tag(self):
        return self.lines[0].tag


def decode(data):
    if data.startswith(codecs.BOM_UTF8):
        return data[3:].decode('utf-8'), 'utf-8', True
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode('utf-16'), 'utf-16', False
    try:
        return data.decode('utf-8'), 'utf-8', False
    except UnicodeDecodeError:
        return data.decode('cp1252'), 'cp1252', False


class Gedcom:
    def __init__(self, text):
        self.records = []
        for raw in re.split(r'\r\n|\n|\r', text):
            if not raw.strip():
                continue
            m = LINE_RE.match(raw)
            ln = (Line(int(m.group(2)), m.group(3), m.group(4), m.group(5), m.group(1), raw)
                  if m else Line(99, None, '?', None, '', raw))
            if ln.level == 0 or not self.records:
                self.records.append(Record())
            self.records[-1].lines.append(ln)
        cnt = collections.defaultdict(collections.Counter)
        for r in self.records:
            for l in r.lines:
                if l.level < 99:
                    cnt[l.level][l.indent] += 1
        self._indents = {lv: c.most_common(1)[0][0] for lv, c in cnt.items()}
        self.index()

    def index(self):
        self.by_xref = {r.xref: r for r in self.records if r.xref}

    def indi(self):
        return [r for r in self.records if r.tag == 'INDI']

    def fams(self):
        return [r for r in self.records if r.tag == 'FAM']

    def nl(self, level, tag, value=None):
        return Line(level, None, tag, value, self._indents.get(level, ''))

    def add_record(self, rec):
        i = len(self.records)
        if self.records and self.records[-1].tag == 'TRLR':
            i -= 1
        self.records.insert(i, rec)
        self.index()

    def dump(self, eol):
        return eol.join(l.text() for r in self.records for l in r.lines) + eol


def l1_blocks(rec):
    out, L, i = [], rec.lines, 1
    while i < len(L):
        if L[i].level == 1:
            j = i + 1
            while j < len(L) and L[j].level > 1:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def find_l1(rec, tag):
    for s, e in l1_blocks(rec):
        if rec.lines[s].tag == tag:
            return s, e
    return None


def sub(rec, s, e, tag, level=2):
    for k in range(s + 1, e):
        if rec.lines[k].level == level and rec.lines[k].tag == tag:
            return k
    return None


def ptrs(rec, tag):
    return [rec.lines[s].value.strip() for s, e in l1_blocks(rec)
            if rec.lines[s].tag == tag and rec.lines[s].value]


def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s).strip().lower()


def name_parts(rec):
    b = find_l1(rec, 'NAME')
    if not b:
        return '', ''
    v = rec.lines[b[0]].value or ''
    m = NAME_RE.match(v)
    return (m.group(1).strip(), m.group(2).strip()) if m else (v.strip(), '')


def sex(rec):
    b = find_l1(rec, 'SEX')
    return (rec.lines[b[0]].value or '').strip().upper() if b else ''


def event_years(rec, tag='BIRT'):
    b = find_l1(rec, tag)
    if not b:
        return []
    k = sub(rec, b[0], b[1], 'DATE')
    if k is None:
        return []
    return [int(y) for y in YEAR_RE.findall(rec.lines[k].value or '')]


class Report:
    def __init__(self):
        self.sections = collections.OrderedDict()

    def add(self, sec, text):
        self.sections.setdefault(sec, []).append(text)

    def md(self):
        out = ['# Relatório de processamento GEDCOM\n']
        for sec, items in self.sections.items():
            out.append(f'\n## {sec} ({len(items)})\n')
            out += [f'- {t}' for t in items]
        return '\n'.join(out) + '\n'


# ----------------------------------------------------------------- locais ---
STATE_ABBR = {'ac': 'Acre', 'al': 'Alagoas', 'ap': 'Amapá', 'am': 'Amazonas', 'ba': 'Bahia',
              'ce': 'Ceará', 'df': 'Distrito Federal', 'es': 'Espírito Santo', 'go': 'Goiás',
              'ma': 'Maranhão', 'mt': 'Mato Grosso', 'ms': 'Mato Grosso do Sul',
              'mg': 'Minas Gerais', 'pa': 'Pará', 'pb': 'Paraíba', 'pr': 'Paraná',
              'pe': 'Pernambuco', 'pi': 'Piauí', 'rj': 'Rio de Janeiro',
              'rn': 'Rio Grande do Norte', 'rs': 'Rio Grande do Sul', 'ro': 'Rondônia',
              'rr': 'Roraima', 'sc': 'Santa Catarina', 'sp': 'São Paulo', 'se': 'Sergipe',
              'to': 'Tocantins'}
STATE_FULL = {norm(v): v for v in STATE_ABBR.values()}
COUNTRIES = {'brasil': 'Brasil', 'brazil': 'Brasil', 'br': 'Brasil',
             'portugal': 'Portugal', 'pt': 'Portugal'}
REGIONS_PT = {'acores': 'Açores', 'madeira': 'Madeira'}
_SE = ['Aracaju', 'Lagarto', 'Itabaiana', 'Estância', 'São Cristóvão', 'Laranjeiras',
       'Nossa Senhora do Socorro', 'Propriá', 'Maruim', 'Capela', 'Simão Dias',
       'Tobias Barreto', 'Riachuelo', 'Japaratuba', 'Neópolis', 'Frei Paulo', 'Carira',
       'Boquim', 'Itaporanga d\'Ajuda', 'Rosário do Catete', 'Santo Amaro das Brotas',
       'Nossa Senhora das Dores', 'Poço Verde', 'Canindé de São Francisco', 'Umbaúba']
CITIES = {norm(c): (c, 'Sergipe') for c in _SE}
CITIES.update({norm(c): (c, st) for c, st in [
    ('Salvador', 'Bahia'), ('Recife', 'Pernambuco'), ('Maceió', 'Alagoas'),
    ('Rio de Janeiro', 'Rio de Janeiro'), ('São Paulo', 'São Paulo')]})


def resolve_place(value):
    """Retorna (novo_valor, status) com status in ok|unchanged|unresolved."""
    parts = [p.strip() for p in value.split(',') if p.strip()]
    if not parts:
        return value, 'unchanged'
    country = None
    if norm(parts[-1]) in COUNTRIES:
        country = COUNTRIES[norm(parts.pop())]
    if not parts:
        return value, 'unchanged'
    if norm(parts[-1]) in REGIONS_PT and country in (None, 'Portugal'):
        parts[-1] = REGIONS_PT[norm(parts[-1])]
        new = ', '.join(parts + ['Portugal'])
    elif country not in (None, 'Brasil'):
        if len(parts) < 2:
            return value, 'unresolved'
        new = ', '.join(parts + [country])
    else:
        state = None
        if len(parts) >= 2:
            l = norm(parts[-1])
            if l in STATE_ABBR:
                state, parts = STATE_ABBR[l], parts[:-1]
            elif l in STATE_FULL:
                state, parts = STATE_FULL[l], parts[:-1]
        if state is None:
            key = norm(parts[-1])
            if key in CITIES:
                city, state = CITIES[key]
                parts = parts[:-1] + [city]
            elif key in STATE_FULL:
                state, parts = STATE_FULL[key], parts[:-1]
            else:
                return value, 'unresolved'
        new = ', '.join(parts + [state, 'Brasil'])
    return new, ('unchanged' if new == value else 'ok')


def fix_places(g, events, report):
    for rec in g.records:
        if rec.tag not in ('INDI', 'FAM'):
            continue
        for s, e in l1_blocks(rec):
            ev = rec.lines[s].tag
            if ev not in events:
                continue
            k = sub(rec, s, e, 'PLAC')
            if k is None or not (rec.lines[k].value or '').strip():
                continue
            old = rec.lines[k].value
            new, st = resolve_place(old)
            if st == 'ok':
                rec.lines[k].set_value(new)
                report.add('Locais expandidos', f'{rec.xref} {ev}: "{old}" -> "{new}"')
            elif st == 'unresolved':
                report.add('Locais NÃO resolvidos (revisar manualmente)',
                           f'{rec.xref} {ev}: "{old}"')


# ---------------------------------------------------------------- homônimos ---
def detect_homonyms(g):
    """Grupos de homônimos calculados ANTES de alterar nomes. Retorna {xref: set(outros)}."""
    groups = collections.defaultdict(set)
    for r in g.indi():
        given, surn = name_parts(r)
        if given:
            groups[('nome', norm(given), norm(surn))].add(r.xref)
    for r in g.indi():
        fams = ptrs(r, 'FAMS')
        if len(fams) < 2:
            continue
        for fid in fams:
            f = g.by_xref.get(fid)
            if not f:
                continue
            for tag in ('HUSB', 'WIFE'):
                for pid in ptrs(f, tag):
                    if pid != r.xref and pid in g.by_xref:
                        given, _ = name_parts(g.by_xref[pid])
                        first = norm(given).split(' ')[0] if given else ''
                        if first:
                            groups[('conjuges', r.xref, first)].add(pid)
    mates = collections.defaultdict(set)
    for members in groups.values():
        if len(members) > 1:
            for m in members:
                mates[m] |= members - {m}
    return mates


def process_names(g, lineage, escape_at, report):
    done = set()
    for rec in g.indi():
        b = find_l1(rec, 'NAME')
        if not b:
            continue
        s, e = b
        line = rec.lines[s]
        v = line.value or ''
        m = NAME_RE.match(v)
        given, surn, rest = ((m.group(1).strip(), m.group(2).strip(), m.group(3)) if m
                             else (v.strip(), '', ''))
        if surn or not given:
            continue
        label = f'{lineage} - {rec.xref}'
        shown = label.replace('@', '@@') if escape_at else label
        line.set_value(f'{given} /[{shown}]/{rest}')
        k = sub(rec, s, e, 'SURN')
        if k is not None:
            rec.lines[k].set_value(shown)
        else:
            gk = sub(rec, s, e, 'GIVN')
            rec.lines.insert((gk if gk is not None else s) + 1, g.nl(line.level + 1, 'SURN', shown))
        done.add(rec.xref)
        report.add('Perfis sem sobrenome desambiguados', f'{rec.xref}: "{v}" -> "{line.value}"')
    return done


def add_notes(g, targets, mates, alive_injected, ref_person, report):
    for xref in sorted(targets):
        rec = g.by_xref[xref]
        if any(rec.lines[s].tag == 'NOTE' and (rec.lines[s].value or '').startswith('ALERTA DE HOMÔNIMO')
               for s, e in l1_blocks(rec)):
            continue
        given, _ = name_parts(rec)
        given = given or 'este perfil'
        fem = sex(rec) == 'F'
        art = ('esta', 'outras homônimas') if fem else ('este', 'outros homônimos')
        lines = [g.nl(1, 'NOTE', f'ALERTA DE HOMÔNIMO: Perfil tratado para isolar {art[0]} '
                                 f'{given} de {art[1]}. Não fundir.')]
        others = sorted(mates.get(xref, []))
        if others:
            lines.append(g.nl(2, 'CONT', 'Indivíduos distintos (não fundir com): ' + ', '.join(others) + '.'))
        if ref_person:
            lines.append(g.nl(2, 'CONT', f'Dados vitais estimados com base na linha de {ref_person}.'))
        if xref in alive_injected:
            lines.append(g.nl(2, 'CONT', 'Status de vida injetado para leitura direta do aplicativo local.'))
        idx = len(rec.lines)
        for s, e in l1_blocks(rec):
            if rec.lines[s].tag in ('FAMC', 'FAMS'):
                idx = s
                break
        rec.lines[idx:idx] = lines
        report.add('Notas anti-fusão (NOTE) inseridas', f'{xref} ({given})' +
                   (f' - distinto de {", ".join(others)}' if others else ''))


# ---------------------------------------------------------- status de vida ---
def classify(rec, cutoff):
    if find_l1(rec, 'DEAT'):
        return 'dead', 'DEAT'
    ys = event_years(rec, 'BIRT')
    if ys:
        return ('alive', 'nascimento>=corte') if max(ys) >= cutoff else ('dead', 'nascimento<corte')
    return 'alive', 'sem data de nascimento'


def anchor(rec):
    for tag in ('BIRT', 'SEX'):
        b = find_l1(rec, tag)
        if b:
            return b[1]
    last = None
    for s, e in l1_blocks(rec):
        if rec.lines[s].tag == 'NAME':
            last = e
    return last or 1


def apply_alive(g, cutoff, report):
    injected, stats = set(), collections.Counter()
    for rec in g.indi():
        status, why = classify(rec, cutoff)
        stats[(status, why)] += 1
        L = rec.lines
        aliv = [(s, e) for s, e in l1_blocks(rec) if L[s].tag == '_ALIV']
        if status == 'alive':
            changed = False
            if aliv:
                s, e = aliv[0]
                if (L[s].value or '').strip().upper() != 'Y':
                    L[s].set_value('Y')
                    changed = True
                for s, e in reversed(aliv[1:]):
                    del L[s:e]
                    changed = True
            new = []
            resn = find_l1(rec, 'RESN')
            if resn is None:
                new.append(g.nl(1, 'RESN', 'PRIVACY'))
            elif (L[resn[0]].value or '').strip().upper() != 'PRIVACY':
                report.add('RESN pré-existente diferente de PRIVACY (mantido)',
                           f'{rec.xref}: RESN {L[resn[0]].value}')
            if not aliv:
                new.append(g.nl(1, '_ALIV', 'Y'))
            if new:
                i = anchor(rec)
                L[i:i] = new
                changed = True
            if changed:
                injected.add(rec.xref)
            if why == 'sem data de nascimento':
                report.add('Vivos presumidos por falta de data de nascimento (revisar)', rec.xref)
        else:
            for s, e in aliv:
                if (L[s].value or '').strip().upper() == 'Y':
                    L[s].set_value('N')
                    report.add('_ALIV Y corrigido para N em falecidos/antigos', rec.xref)
    for (st, why), n in sorted(stats.items()):
        report.add('Resumo de status de vida', f'{st.upper()} ({why}): {n}')
    return injected


# ----------------------------------------------------- lógica biológica -----
def check_ages(g, fix, report):
    all_fids = [int(m.group(1)) for x in g.by_xref for m in [re.fullmatch(r'@F(\d+)@', x)] if m]
    next_id = [max(all_fids or [0]) + 1]

    def new_fam(tag, pid):
        r = Record()
        r.lines.append(Line(0, f'@F{next_id[0]}@', 'FAM', None))
        r.lines.append(g.nl(1, tag, pid))
        next_id[0] += 1
        g.add_record(r)
        return r.xref

    for fam in g.fams():
        fid = fam.xref
        husb, wife, chil = ptrs(fam, 'HUSB'), ptrs(fam, 'WIFE'), ptrs(fam, 'CHIL')
        viol = collections.defaultdict(set)  # (tag, pid) -> filhos
        for c in chil:
            cy = (event_years(g.by_xref[c]) or [None])[0] if c in g.by_xref else None
            if cy is None:
                continue
            for tag, pids, lo, hi in (('WIFE', wife, 12, 60), ('HUSB', husb, 12, None)):
                for p in pids:
                    py = (event_years(g.by_xref[p]) or [None])[0] if p in g.by_xref else None
                    if py is None:
                        continue
                    d = cy - py
                    if d < lo or (hi is not None and d > hi):
                        viol[(tag, p)].add(c)
                        report.add('Incoerências biológicas',
                                   f'{fid}: {"mãe" if tag == "WIFE" else "pai"} {p} ({py}) x filho {c} ({cy}) = {d} anos')
                    elif tag == 'HUSB' and d > 80:
                        report.add('Avisos (pai com mais de 80 anos; não corrigido)',
                                   f'{fid}: pai {p} ({py}) x filho {c} ({cy}) = {d} anos')
        if not fix or not viol:
            continue
        detach_p, detach_c, allc = [], set(), set(chil)
        for (tag, p), kids in viol.items():
            if kids == allc:
                detach_p.append((tag, p))
            else:
                detach_c |= kids
        for tag, p in detach_p:
            for s, e in l1_blocks(fam):
                if fam.lines[s].tag == tag and (fam.lines[s].value or '').strip() == p:
                    del fam.lines[s:e]
                    break
            nf = new_fam(tag, p)
            for s, e in l1_blocks(g.by_xref[p]):
                if g.by_xref[p].lines[s].tag == 'FAMS' and (g.by_xref[p].lines[s].value or '').strip() == fid:
                    g.by_xref[p].lines[s].set_value(nf)
            report.add('Vínculos rompidos (genitor isolado)', f'{p} removido de {fid}; agora em {nf}')
        for c in sorted(detach_c):
            for s, e in l1_blocks(fam):
                if fam.lines[s].tag == 'CHIL' and (fam.lines[s].value or '').strip() == c:
                    del fam.lines[s:e]
                    break
            nf = new_fam('CHIL', c)
            for s, e in l1_blocks(g.by_xref[c]):
                if g.by_xref[c].lines[s].tag == 'FAMC' and (g.by_xref[c].lines[s].value or '').strip() == fid:
                    g.by_xref[c].lines[s].set_value(nf)
            report.add('Vínculos rompidos (filho isolado)', f'{c} removido de {fid}; agora em {nf}')


def validate(g, report):
    for rec in g.records:
        for s, e in l1_blocks(rec):
            l = rec.lines[s]
            if l.tag in ('FAMC', 'FAMS', 'HUSB', 'WIFE', 'CHIL') and l.value and l.value.strip() not in g.by_xref:
                report.add('Validação final: ponteiros quebrados', f'{rec.xref}: {l.tag} {l.value}')
    for fam in g.fams():
        for tag, back in (('HUSB', 'FAMS'), ('WIFE', 'FAMS'), ('CHIL', 'FAMC')):
            for pid in ptrs(fam, tag):
                p = g.by_xref.get(pid)
                if p and fam.xref not in ptrs(p, back):
                    report.add('Validação final: vínculo sem reciprocidade',
                               f'{fam.xref} {tag} {pid}, mas {pid} não tem {back} {fam.xref}')


# ------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input')
    ap.add_argument('-o', '--output')
    ap.add_argument('--lineage', help='Rótulo da linhagem para perfis sem sobrenome (ex: "Linhagem de Sergipe")')
    ap.add_argument('--ref-person', help='Pessoa de referência citada nas NOTEs (ex: "Celso Gomes Gama")')
    ap.add_argument('--current-year', type=int, default=2026)
    ap.add_argument('--cutoff-age', type=int, default=116)
    ap.add_argument('--events', default='BIRT,DEAT,MARR', help='Eventos cujo PLAC será expandido')
    ap.add_argument('--places-map', help='JSON extra: {"lagarto": ["Lagarto", "Sergipe"]}')
    ap.add_argument('--fix-ages', action='store_true', help='Rompe vínculos biologicamente impossíveis')
    ap.add_argument('--no-notes', action='store_true')
    ap.add_argument('--escape-at', action='store_true', help='Duplica @ dentro de NAME/SURN (GEDCOM estrito)')
    ap.add_argument('--dry-run', action='store_true', help='Só diagnóstico; não grava saída')
    a = ap.parse_args()

    if not a.dry_run and not (a.output and a.lineage):
        ap.error('informe -o e --lineage (ou use --dry-run)')
    if a.places_map:
        for k, v in json.loads(Path(a.places_map).read_text(encoding='utf-8')).items():
            CITIES[norm(k)] = (v[0], v[1])

    text, enc, bom = decode(Path(a.input).read_bytes())
    eol = '\r\n' if '\r\n' in text else '\n'
    g, rep = Gedcom(text), Report()
    n_indi, n_fam = len(g.indi()), len(g.fams())
    cutoff = a.current_year - a.cutoff_age
    lineage = a.lineage or 'LINHAGEM'

    mates = detect_homonyms(g)
    nameless = process_names(g, lineage, a.escape_at, rep)
    fix_places(g, {e.strip().upper() for e in a.events.split(',')}, rep)
    injected = apply_alive(g, cutoff, rep)
    if not a.no_notes:
        add_notes(g, nameless | set(mates), mates, injected, a.ref_person, rep)
    check_ages(g, a.fix_ages, rep)
    validate(g, rep)
    if a.escape_at is False and nameless:
        rep.add('Atenção', 'NAME/SURN contêm "@ID@" com @ simples (como no modelo pedido). '
                           'Parsers estritos podem exigir @@; use --escape-at se der erro de importação.')
    rep.add('Totais', f'INDI: {n_indi} | FAM: {n_fam} -> {len(g.fams())} | corte de vida: nascidos em {cutoff} ou depois')

    md = rep.md()
    if a.dry_run:
        print(md)
        return
    out = Path(a.output)
    data = g.dump(eol).encode(enc)
    out.write_bytes((codecs.BOM_UTF8 + data) if bom else data)
    Path(str(out) + '.relatorio.md').write_text(md, encoding='utf-8')
    print(md)
    print(f'\nGravado: {out}  (+ {out}.relatorio.md)')


if __name__ == '__main__':
    main()
