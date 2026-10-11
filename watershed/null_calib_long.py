#!/usr/bin/env python3
"""Season-length null calibration: K=20 nudged members, 168 ticks (a 7-day season), output null_calib_long.jsonl.
The 24-tick run showed the control's rank spreading with time (sd 0.04 at 4 ticks, 0.14 at 24, uniform 0.29),
so a 24-tick calibration cannot stand in for a full season."""
import os, runpy
os.environ.update(K='20', TT='168', OUT='null_calib_long.jsonl')
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'null_calib.py'), run_name='__main__')
