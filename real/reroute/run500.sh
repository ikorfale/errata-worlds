#!/bin/bash
set -e; cd "$(dirname "$0")"
python3 prep500.py 500
read n m < <(python3 -c "import json;M=json.load(open('polar500.meta.json'));print(M['n'],M['m'])")
./route polar500.f32 $n $m polar500.dx.f32 500 1 polar500_me
python3 analyse500.py polar500 polar500_me reroute500.json
echo __END__
