"""Render a heightmap: hypsometric colours + hillshade, sea below 0."""
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LightSource

LAND = LinearSegmentedColormap.from_list("land", ["#3f7d4e", "#8aa65a", "#c9b77a", "#9c7b5b", "#7a6a64", "#f2efe9"])
SEA = LinearSegmentedColormap.from_list("sea", ["#16324f", "#2f6a8f", "#7fb3c8"])

def rgb(h, sea=0.0, rivers=None):
    ls = LightSource(azdeg=315, altdeg=40)
    hl = np.clip((h - sea) / max(h.max() - sea, 1e-9), 0, 1)
    hs = np.clip((h - h.min()) / max(sea - h.min(), 1e-9), 0, 1)
    col = np.where((h > sea)[..., None], LAND(hl)[..., :3], SEA(hs)[..., :3])
    shade = ls.hillshade(h * 300, vert_exag=1, dx=1, dy=1)
    out = col * (0.55 + 0.45 * shade[..., None])
    out = np.where((h > sea)[..., None], out, col)
    if rivers is not None:
        w = np.clip(rivers, 0, 1)[..., None]
        out = out * (1 - w) + np.array([0.18, 0.42, 0.65]) * w
    return np.clip(out, 0, 1)

def save(h, path, title=None, rivers=None, h0=None):
    if h0 is not None:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6.3), dpi=110)
        for a, z, t in zip(ax, [h0, h], ["before: noise", "after: rain"]):
            a.imshow(rgb(z, rivers=None if z is h0 else rivers)); a.set_axis_off(); a.set_title(t, fontsize=12)
    else:
        fig, a = plt.subplots(figsize=(7, 7), dpi=110); a.imshow(rgb(h, rivers=rivers)); a.set_axis_off()
    if title: fig.suptitle(title, fontsize=13)
    fig.tight_layout(); fig.savefig(path, facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    import sys
    p = sys.argv[1]
    save(np.load(p + "_h.npy"), p + "_pair.png", h0=np.load(p + "_h0.npy"))
