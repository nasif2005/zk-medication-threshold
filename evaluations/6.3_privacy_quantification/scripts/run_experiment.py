#!/usr/bin/env python3
import argparse, subprocess, sys
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--samples",type=int,default=10000);ap.add_argument("--seed",type=int,default=20260813);a=ap.parse_args(); scripts=Path(__file__).resolve().parent
    subprocess.run([sys.executable,str(scripts/"generate_workload.py"),"--samples",str(a.samples),"--seed",str(a.seed)],check=True)
    subprocess.run([sys.executable,str(scripts/"analyze_privacy.py")],check=True)
if __name__ == "__main__": main()
