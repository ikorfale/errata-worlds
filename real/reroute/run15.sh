#!/bin/bash
set -e; cd "$(dirname "$0")"
read n m dy < <(python3 prep15.py)
./route g15.f32 $n $m g15.dx.f32 $dy 1 g15_me
echo routed
