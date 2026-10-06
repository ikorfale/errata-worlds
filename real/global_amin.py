"""#166: A_min sweep (10/30/100/300 km2) of Hack's h on HydroRIVERS mouths, per region and pooled (all 9, and without gr)."""
import numpy as np, json
from hack import load, fit
rng = np.random.default_rng(1); res = {}; pool = {}
REG = ('af', 'ar', 'as', 'au', 'eu', 'gr', 'na', 'sa', 'si'); AM = (10, 30, 100, 300)
for reg in REG:
    d = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    o = (d['NEXT_DOWN'] == 0) & (d['UPLAND_SKM'] >= 10) & (d['UPLAND_SKM'] <= 1e6) & (d['DIST_UP_KM'] > 0)
    A, L = d['UPLAND_SKM'][o], d['DIST_UP_KM'][o]; pool[reg] = (A, L); del d
    line = []
    for am in AM:
        s = A >= am; r = fit(A[s], L[s], rng, 200); res[f'{reg} A>={am}'] = r; line.append(f'{r["h"]:.3f}({r["n"]})')
    print(reg, ' '.join(line), flush=True)
for name, regs in (('all9', REG), ('without_gr', [r for r in REG if r != 'gr'])):
    A = np.concatenate([pool[r][0] for r in regs]); L = np.concatenate([pool[r][1] for r in regs]); line = []
    for am in AM:
        s = A >= am; r = fit(A[s], L[s], rng, 300); res[f'{name} A>={am}'] = r; line.append(f'{r["h"]:.3f} [{r["ci"][0]:.3f},{r["ci"][1]:.3f}] ({r["n"]})')
    print(name, ' | '.join(line), flush=True)
json.dump(res, open('out/global_amin.json', 'w'), default=float); print('__END__')
