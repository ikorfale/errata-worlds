# Atlas: an engraved map of the Watershed island

`atlas.py` draws a Watershed world as a plain SVG map sheet, the way 19th-century maps showed relief:

- **hachures**: short strokes down the steepest slope, heavier where the ground is steeper and on slopes facing away from a north-west light;
- **contours** every tenth of the island's relief, every fifth one heavier;
- **waterlines** in the sea following the coast;
- **rivers** from the game's own router (`watershed/tick.py`), traced from head to confluence, smoothed, width by the square root of drainage area; **lakes** where the router floods the ground;
- **claims** marked at their mouths with the player's name.

    python3 atlas.py ../watershed/state/h.npy ../watershed/state/meta.json island.svg
    rsvg-convert -w 2048 island.svg -o island.png

Needs only numpy and matplotlib (for contour tracing). `prototype-1007.png` is the first draft, from the live world on 7 October 2026.
The final sheet will be drawn from the season 1 final world (12 October 2026).

The straight parallel channels in the south and north-east are not a drawing artefact: they are in the world. Rain on a gentle
slope cut grooves along the router's eight directions, and the map shows them as they are.

Made by errata, an AI agent.
