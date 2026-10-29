"""Runs the pipeline in order: 01 core estimates -> 02 static backtests -> 03 reviewer checks -> figures. About 2 minutes on an Apple M1 Pro."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
for s in ["01_core_estimates.py", "02_backtests_static.py", "03_reviewer_checks.py", "figures.py"]:
    print("==", s); subprocess.run([sys.executable, os.path.join(HERE, s)], check=True)
