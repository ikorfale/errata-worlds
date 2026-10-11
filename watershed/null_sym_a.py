#!/usr/bin/env python3
"""null_sym.py, seeds [0:11]"""
import os, runpy
os.environ.update(SLICE="0:11")
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "null_sym.py"), run_name="__main__")
