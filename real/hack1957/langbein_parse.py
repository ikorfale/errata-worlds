"""Parse tesseract output of Langbein et al. 1947 (WSP 968-C) summary table, pp. 145-155.
Keeps drainage area (sq mi) and longest watercourse (mi). Rows are kept only if internally
consistent: basin altitude max >= mean >= min in the three columns after the lengths, average land slope between E-W and N-S, stream density 0.3-6, and Lca = Sal/A between 0.15 and 0.9 of the longest
watercourse. No filter uses the L-A relation itself."""
import re, glob, csv
NUM = re.compile(r'(?<![\d.])(\d{1,3}(?:,\s?\d{3})+(?!\d)|\d+,\d{1,2}(?!\d)|\d+\.\s?\d+|\.\d+|\d+)(?![\d])')
out = []; seen = set(); bad = 0; tried = 0
for f in sorted(glob.glob('lb/o*.txt')):
    for line in open(f):
        m = re.match(r'^\s*([0-9I])\s*[-~+.]\s*(\d{2,4}[A-Z]?(?:[.,]\s?\d)?)', line)
        if not m: continue
        tried += 1
        sid = m.group(1).replace('I', '1') + '-' + m.group(2).replace(' ', '')
        rest = line[m.end():]
        # name ends at the last run of 2+ dots/dashes/underscores before the numbers
        cut = [mm.end() for mm in re.finditer(r'[._\-—]{2,}|[|\]}]', rest)]
        # take numbers after the first cut that is followed by digits
        body = None
        for c in cut:
            if re.match(r'[\s|\]})!;:,*]*\d', rest[c:]) or re.match(r'[\s|\]})!;:,*]*\.\d', rest[c:]):
                body = rest[c:]; break
        if body is None: bad += 1; continue
        toks = []
        for t in NUM.findall(body):
            t = t.replace(' ', '')
            if ',' in t and re.fullmatch(r'\d{1,3}(,\d{3})+', t): t = t.replace(',', '')
            elif ',' in t: t = t.replace(',', '.')  # OCR comma used as decimal point
            toks.append(t)
        if len(toks) < 13: bad += 1; continue
        try:
            A, dens, sal = float(toks[0]), float(toks[1]), float(toks[2]); Llong, Lpr = float(toks[8]), float(toks[9])
        except ValueError: bad += 1; continue
        try: ew, ns, avg = float(toks[3]), float(toks[4]), float(toks[5])
        except ValueError: bad += 1; continue
        try: amax, amean, amin = float(toks[10]), float(toks[11]), float(toks[12])
        except ValueError: bad += 1; continue
        # altitude max >= mean >= min pins the columns right after the two lengths
        if not (amax >= amean >= amin and amax >= 100 and Lpr < amax): bad += 1; continue
        ok = 0.95*min(ew, ns) <= avg <= 1.05*max(ew, ns) and 0.3 <= dens <= 6 and A > 0 and Llong > 0 and 0.15 <= (sal / A) / Llong <= 0.9
        if not ok: bad += 1; continue
        if sid in seen: continue
        seen.add(sid); out.append((sid, A, Llong, Lpr, f[4:-4]))
w = csv.writer(open('langbein1947.csv', 'w')); w.writerow(['station', 'A_sqmi', 'L_longest_mi', 'L_principal_mi', 'page'])
w.writerows(out)
print(f'row-like lines {tried}, kept {len(out)}, rejected {bad}')
