"""Run the full pipeline: generate -> profile -> audit -> diagrams -> build -> site -> validate."""
import runpy
import sys

for step in ["generate_companion_data", "profile_data", "dq_audit", "build_deliverables", "build_diagrams", "build_site", "validate"]:
    print(f"\n=== {step} ===")
    try:
        runpy.run_module(step, run_name="__main__")
    except SystemExit as e:
        if e.code:
            sys.exit(e.code)
