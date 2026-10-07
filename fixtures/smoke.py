"""Harmless public fixture. No private code, no network, no secrets.
1) real git: init repo, commit, compare-and-swap ref update (stale CAS must fail);
2) synthetic credential-shape pattern guard refuses without echoing content."""
import os, re, subprocess, tempfile

def git(repo, *a, check=True):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=check)

with tempfile.TemporaryDirectory() as d:
    git(d, "init", "-q", "-b", "main")
    git(d, "config", "user.email", "ci@example.invalid"); git(d, "config", "user.name", "ci")
    open(os.path.join(d, "a.txt"), "w").write("one\n")
    git(d, "add", "a.txt"); git(d, "commit", "-qm", "one")
    c1 = git(d, "rev-parse", "HEAD").stdout.strip()
    open(os.path.join(d, "a.txt"), "w").write("two\n")
    git(d, "commit", "-qam", "two")
    c2 = git(d, "rev-parse", "HEAD").stdout.strip()
    assert git(d, "update-ref", "refs/heads/state", c1, "0" * 40, check=False).returncode == 0
    assert git(d, "update-ref", "refs/heads/state", c2, c1, check=False).returncode == 0
    assert git(d, "update-ref", "refs/heads/state", c1, c1, check=False).returncode != 0, "stale CAS accepted"
    print("PASS git-cas")

PAT = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,})")
fake = "gh" + "p_" + "A" * 36  # synthetic
assert PAT.search("x " + fake) and not PAT.search("harmless text")
print("PASS pattern-guard (content not echoed)")
