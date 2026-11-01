"""Parse a SuperWEB2 CSV export (Geography rows × Age × Population group columns)
into a long table: ward, age, group, persons. Semicolon-separated, decimal comma."""
import csv, sys, re
src, out = sys.argv[1], sys.argv[2]
rows = list(csv.reader(open(src, encoding='utf-8-sig'), delimiter=';'))
ai = next(i for i, r in enumerate(rows) if r and r[0] in ('Age in completed years', 'Age'))
ages_hdr, grp_hdr = rows[ai], rows[ai + 1]
cols, age = [], None
for j in range(1, len(grp_hdr)):
    if j < len(ages_hdr) and ages_hdr[j]:
        age = ages_hdr[j]
    if grp_hdr[j]:
        cols.append((j, age, grp_hdr[j]))
n = 0
with open(out, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['ward', 'ward_label', 'age', 'group', 'persons'])
    for r in rows[ai + 2:]:
        if not r or not re.match(r'^\d{8}', r[0] or ''):
            continue
        code = r[0][:8]
        for j, a, g in cols:
            if a == 'Total' or g == 'Total':
                continue
            v = r[j].replace(',', '.') if j < len(r) else ''
            w.writerow([code, r[0], a, g, v or '0']); n += 1
print('rows written', n, 'groups', sorted({g for _, _, g in cols}), 'ages', len({a for _, a, _ in cols}))
