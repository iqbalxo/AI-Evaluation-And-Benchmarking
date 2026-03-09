"""Wrapper to run test_judge and capture output to a UTF-8 file."""
import sys
import io
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Redirect stdout to a file
out_file = open("test_fallback_result.txt", "w", encoding="utf-8")
old_stdout = sys.stdout
sys.stdout = out_file

from test_judge import run_tests
try:
    success = run_tests(fallback_only=False)
finally:
    sys.stdout = old_stdout
    out_file.close()

# Print just the exit status to console
print(f"Tests {'PASSED' if success else 'FAILED'}")
sys.exit(0 if success else 1)
