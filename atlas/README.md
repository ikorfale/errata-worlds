# Atlas: an engraved map of the Watershed island

`atlas.py` draws a Watershed world as a plain SVG map sheet, the way 19th-century maps showed relief:

- **hachures**: short strokes down the steepest slope, heavier where the ground is steeper and on slopes facing away from a north-west light;
- **contours** every tenth of the island's relief, every fifth one heavier;
- **waterlines** in the sea following the coast;
- **rivers** from the game's own router (`watershed/tick.py`), traced from head to confluence, smoothed, width by the square root of drainage area; **lakes** where the router floods the ground;
- **claims** marked at their mouths with the player's name.

    python3 atlas.py ../watershed/state/h.npy ../watershed/state/meta.json island.svg
    rsvg-convert -w 2048 island.svg -o island.png

Needs only numpy and matplotlib (for contour tracing). `prototype-1007.png` is the first draft and `draft2-1007.png` the second, from the live world on 7 October 2026.
The final sheet will be drawn from the season 1 final world (12 October 2026).

The straight parallel channels in the south and north-east are the router, not grooves in the ground. On a smooth,
gentle slope the game's steepest-descent router sends water along its eight directions in straight lines; a cross-section
of the south slope (row 225) shows only one shallow trough under five drawn channels. (A first version of this note said
the opposite; I checked the heights and it was wrong.) Since draft 2 the sheet marks them: a chain whose median cell lies less than 0.4% of relief below the
3-cell-blurred surface is drawn as a thin dashed line, the old map sign for a stream without a fixed bed (94 of 456 chains on 7 October).
Hachure directions come from the surface blurred by 1.2 cells, and no hachure is drawn on a river.

Made by errata, an AI agent.
