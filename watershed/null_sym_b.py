#!/usr/bin/env python3
"""null_sym.py, seeds [11:21]"""
import os, runpy
os.environ.update(SLICE="11:21")
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "null_sym.py"), run_name="__main__")
