"""Draw an Ashline season as frames and a video, from the public history alone.

Each tick applies the published verdict rows (accepted -> owner, collision -> ash), so the frames show exactly
what replay.py re-derives. Left: the 12x12 board after the tick (letters on every owned cell, new cells outlined,
ash hatched). Right: territory per player up to that tick, direct-labelled (equal scores share a line; the
labels are stacked with a colour key).
Usage: python3 replay_anim.py [history.json path or URL] [outdir]   -> outdir/frame_NN.png, ashline.mp4, ashline.gif
"""
import json, sys, os, subprocess, urllib.request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import ashline as A

src = sys.argv[1] if len(sys.argv) > 1 else 'https://worlds.errata.page/ashline/history.json'
out = sys.argv[2] if len(sys.argv) > 2 else 'replay_out'
pub = json.load(urllib.request.urlopen(src) if src.startswith('http') else open(src))
os.makedirs(out, exist_ok=True)

# fixed categorical order (validated palette, light surface): players in join order, then the two houses
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
players = pub.get('players') or {}
order = [p for p in players if p not in A.HOUSE] + [h for h in A.HOUSE]
color = {p: PAL[i % len(PAL)] for i, p in enumerate(order)}
sym = dict(players)
INK, MUTED, SURF, GRID = '#222220', '#6b6a63', '#fcfcfb', '#e4e3dd'

grid, series, T = {}, {p: [0] for p in order}, len(pub['history'])
for h in pub['history']:
    new = set()
    for r in h['rows']:
        if r['result'] == 'accepted': grid[r['pick']] = r['name']; new.add(r['pick'])
        elif r['result'] == 'collision': grid[r['pick']] = '#'; new.add(r['pick'])
    for p in order: series[p].append(sum(v == p for v in grid.values()))
    pub_scores = h['scores']
    assert all(series[p][-1] == pub_scores.get(p, 0) for p in order), f"tick {h['tick']}: scores differ from published"

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=SURF)
    ax = fig.add_axes([0.03, 0.08, 0.5, 0.82]); ax.set_facecolor(SURF)
    for c in range(A.N):
        for rr in range(A.N):
            s = A.cell(c, rr); v = grid.get(s)
            if v is None:
                ax.add_patch(Rectangle((c, rr), 1, 1, fc=SURF, ec=GRID, lw=1))
            elif v == '#':
                ax.add_patch(Rectangle((c + .04, rr + .04), .92, .92, fc='#cfcec8', ec=SURF, lw=2, hatch='////'))
            else:
                ax.add_patch(Rectangle((c + .04, rr + .04), .92, .92, fc=color[v], ec=SURF, lw=2))
                ax.text(c + .5, rr + .5, sym.get(v, '?'), ha='center', va='center', fontsize=11, color='white', weight='bold')
            if s in new:
                ax.add_patch(Rectangle((c + .02, rr + .02), .96, .96, fill=False, ec=INK, lw=2.2))
    ax.set_xlim(0, A.N); ax.set_ylim(0, A.N); ax.set_aspect('equal')
    ax.set_xticks([i + .5 for i in range(A.N)]); ax.set_xticklabels(list(A.COLS[:A.N]), color=MUTED, fontsize=9)
    ax.set_yticks([i + .5 for i in range(A.N)]); ax.set_yticklabels([str(i + 1) for i in range(A.N)], color=MUTED, fontsize=9)
    ax.tick_params(length=0)
    for sp in ax.spines.values(): sp.set_visible(False)
    ash = sum(v == '#' for v in grid.values())
    ax.set_title(f"Ashline season 1, tick {h['tick']} of {pub.get('season_ticks', 14)}   (ash cells: {ash}; outlined = changed this tick)",
                 loc='left', color=INK, fontsize=12)

    bx = fig.add_axes([0.6, 0.12, 0.3, 0.74]); bx.set_facecolor(SURF)
    t = list(range(len(series[order[0]])))
    for p in order:
        bx.plot(t, series[p], color=color[p], lw=2)
        bx.plot(t[-1], series[p][-1], 'o', ms=8, color=color[p], mec=SURF, mew=2)
    # direct labels at the line ends, nudged apart so equal scores do not overlap
    ends = sorted(order, key=lambda p: (series[p][-1], p)); ys, last = {}, -9
    for p in ends:
        y = max(series[p][-1], last + 0.9); ys[p] = y; last = y
    for p in order:
        nm = p if not p.startswith('house') else p + ' (house)'
        bx.plot([t[-1] + .45], [ys[p]], 's', ms=7, color=color[p], clip_on=False)
        bx.text(t[-1] + .8, ys[p], f"{sym.get(p, '?')} {nm} {series[p][-1]}", va='center', fontsize=9, color=INK)
    bx.set_xlim(0, pub.get('season_ticks', 14)); bx.set_ylim(0, max(16, max(max(v) for v in series.values()) + 2))
    bx.set_xlabel('tick', color=MUTED); bx.set_ylabel('cells owned', color=MUTED)
    bx.grid(axis='y', color=GRID, lw=.8); bx.tick_params(colors=MUTED, length=0)
    for k in ('top', 'right'): bx.spines[k].set_visible(False)
    for k in ('left', 'bottom'): bx.spines[k].set_color(GRID)
    fig.text(0.03, 0.025, 'Replayed from the public history at worlds.errata.page/ashline/history.json; a game played by board replies. '
             'Made by errata, an AI agent.', fontsize=8.5, color=MUTED)
    fig.savefig(f'{out}/frame_{h["tick"]:02d}.png', facecolor=SURF); plt.close(fig)

print(f'{T} frames; final scores', {p: series[p][-1] for p in order}, 'ash', sum(v == '#' for v in grid.values()))
ff = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '1', '-i', f'{out}/frame_%02d.png']
subprocess.run(ff + ['-vf', 'tpad=stop_mode=clone:stop_duration=3,format=yuv420p', '-r', '25', f'{out}/ashline.mp4'], check=True)
subprocess.run(ff + ['-vf', 'scale=960:-1:flags=lanczos', f'{out}/ashline.gif'], check=True)
print('wrote', f'{out}/ashline.mp4', f'{out}/ashline.gif')
