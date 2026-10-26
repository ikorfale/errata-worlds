"""Partner cost of pact defection, from s2_defect.txt (Fable 26.10: Part B review flagged that I never
reported the partner's score, only the defector's). Parses the 'score' column (all seats) that run() already
prints, pairs each single-defector row against its pact's honest-pact row, same seeds (common random numbers),
and reports both the defector's gain over honest and the partner's gain over honest side by side.
Usage: python3 s2_defect_partner.py [s2_defect.txt]
"""
import re, sys

SEATS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']


def parse_scores(line):
    m = re.search(r'score ([\d\. ]+?)\s+decided', line)
    return dict(zip(SEATS, [float(x) for x in m.group(1).split()]))


def main(path):
    honest = {}
    rows = []
    for raw in open(path):
        if not raw.strip() or raw.startswith('    '):
            continue
        l = raw.strip()
        toks = l.split()
        label = toks[0]
        if label == 'no':
            continue
        sc = parse_scores(l)
        if label == 'pact':
            honest[tuple(toks[1].split('+'))] = sc
            continue
        if '+' in toks[1]:
            continue  # both-defect rows: no single partner to report
        rows.append((label, toks[1], toks[2], sc))

    for mode, who, k, sc in rows:
        pair = next(p for p in honest if who in p)
        partner = [x for x in pair if x != who][0]
        h = honest[pair]
        d_gain = sc[who] - h[who]
        p_gain = sc[partner] - h[partner]
        print(f"{mode:6} {who} {k}: defector {who} {d_gain:+.3f} (honest {h[who]:.2f}->{sc[who]:.2f})"
              f"  partner {partner} {p_gain:+.3f} (honest {h[partner]:.2f}->{sc[partner]:.2f})")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 's2_defect.txt')
