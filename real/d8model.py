"""Expected NS:EW D8 code ratio if D8 is run on a lat/long grid as if cells were square,
for isotropic true gradient directions: index-space direction tan(phi) = tan(theta)/cos(lat) for the N-S component.
Cardinal code wins within +-22.5 deg of its axis (ESRI D8 on a plane, diagonal distance sqrt2)."""
import numpy as np
th = np.random.default_rng(1).uniform(0, 2*np.pi, 2_000_000)
for lat in (0, 25, 62.5, 67.5, 72.5, 77.5, 82):
    gx, gy = np.cos(th) * np.cos(np.radians(lat)), np.sin(th)   # E-W gradient per column shrinks with cos(lat)
    phi = np.degrees(np.arctan2(gy, gx)) % 180
    ew = ((phi < 22.5) | (phi > 157.5)).mean(); ns = (np.abs(phi - 90) < 22.5).mean()
    print(f'lat {lat:5.1f}: NS {ns*100:5.1f}%  EW {ew*100:5.1f}%  NS:EW {ns/ew:5.2f}')
