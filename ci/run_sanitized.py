#!/usr/bin/env python3
"""Run private validation with ALL candidate output captured privately on the runner.
Prints/publishes only a fixed-schema JSON summary (no source text, traces or paths)."""
import json, os, re, subprocess, sys
MODE = os.environ["MODE"]; CAND = os.environ.get("CAND", "")
WS = os.environ["GITHUB_WORKSPACE"]; TMP = os.environ["RUNNER_TEMP"]
LOG = open(os.path.join(TMP, "private-output.log"), "w")     # never uploaded or printed
ENV = {k: v for k, v in os.environ.items()
       if k in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "RUNNER_TEMP")}
ENV["GIT_TERMINAL_PROMPT"] = "0"

def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace", timeout=600)
    LOG.write(r.stdout); return r.returncode, r.stdout

def credential_clean():
    hits = 0
    for d in (os.path.expanduser("~/.ssh"), TMP):
        for root, _, files in os.walk(d):
            for f in files:
                try:
                    with open(os.path.join(root, f), "rb") as fh:
                        if b"PRIVATE KEY" in fh.read(1 << 20): hits += 1
                except OSError: pass
    _, cfg = run(["git", "config", "--list", "--show-origin"], os.path.join(WS, "candidate"))
    if re.search(r"sshcommand|extraheader", cfg, re.I): hits += 1
    return hits == 0

def unit(out):
    ran = re.findall(r"^Ran (\d+) tests?", out, re.M)
    sk = re.findall(r"skipped=(\d+)", out)
    return {"ran": int(ran[-1]) if ran else 0, "skipped": int(sk[-1]) if sk else 0,
            "ok": bool(re.search(r"^OK\b", out, re.M))}

S = {"schema": 1, "mode": MODE, "candidate": CAND or None}
if MODE.startswith("selftest"):
    rc, out = run([sys.executable, os.path.join(WS, "validator/fixtures/leaky.py"), MODE], WS)
    S.update(selftest_exit=rc, captured_bytes=len(out))
    ok = (rc == 0) if MODE == "selftest-pass" else False
else:
    c = os.path.join(WS, "candidate")
    _, head = run(["git", "rev-parse", "HEAD"], c)
    S["fetched_head_matches"] = head.strip() == CAND
    S["credentials_cleaned_before_candidate_code"] = credential_clean()
    if not (S["fetched_head_matches"] and S["credentials_cleaned_before_candidate_code"]):
        ok = False
    else:
        rc, out = run([sys.executable, "-m", "unittest", "tests.test_coord"], c)
        S["test_coord"] = dict(unit(out), exit=rc)
        mods = {}
        for m in ("test_intake", "test_regressions", "test_manifest", "test_verify_remote",
                  "test_checkpoint"):
            r2, o2 = run([sys.executable, "-m", "unittest", "tests." + m], c)
            mods[m] = dict(unit(o2), exit=r2)
        S["suites"] = mods
        rc, out = run(["sh", "verify.sh"], c)
        S["verify_sh_exit"] = rc
        S["verify_all_passed_line"] = "verify.sh: ALL CHECKS PASSED" in out
        S["gate_not_run_lines"] = len(re.findall(r"^NOT-RUN", out, re.M))
        S["gate_fail_lines"] = len(re.findall(r"^FAIL", out, re.M))
        tc = S["test_coord"]
        ok = (rc == 0 and S["verify_all_passed_line"] and S["gate_not_run_lines"] == 0
              and tc["exit"] == 0 and tc["ok"] and tc["ran"] > 0 and tc["skipped"] == 0
              and all(v["exit"] == 0 and v["ran"] > 0 for v in mods.values()))
S["result"] = "pass" if ok else "fail"
LOG.close()
line = json.dumps(S, sort_keys=True)
print("SANITIZED-SUMMARY " + line)
with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
    f.write("### private-validate\n\n```json\n" + line + "\n```\n")
sys.exit(0 if ok else 1)
