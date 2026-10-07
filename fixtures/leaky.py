"""Synthetic sensitive-looking output to prove suppression. All values are fake."""
import sys
fake = "gh" + "p_" + "SYNTHETICLEAKMARKER0000000000000000000"
print("SYNTHETIC-LEAK-MARKER stdout " + fake)
print("-----BEGIN SYNTHETIC-LEAK-MARKER KEY-----", file=sys.stderr)
print('Traceback (most recent call last):\n  File "/private/SYNTHETIC-LEAK-MARKER.py"', file=sys.stderr)
sys.exit(0 if sys.argv[1] == "selftest-pass" else 1)
