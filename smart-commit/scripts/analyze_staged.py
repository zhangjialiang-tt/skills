#!/usr/bin/env python3
"""smart-commit: deterministic staged-analysis helper (read-only).

Runs the pre-flight + layered-diff + sensitive-scan + split-signal checks that
SKILL.md step 1 describes, and prints a structured report for the agent to
consume. It never modifies the repository.

Usage:
    python scripts/analyze_staged.py [--repo PATH] [--json]

Exit code is always 0 on successful analysis; "stop / warn / execute" is a
decision the agent makes from the printed fields, not an error.
"""
import json
import os
import re
import subprocess
import sys

PROTECTED_BRANCHES = {"main", "master", "production", "release", "prod"}
BIG_FILE_THRESHOLD = 20
BIG_LINE_THRESHOLD = 2000
DIFF_SCAN_CAP = 1_500_000  # chars; cap sensitive scan on very large diffs

SENSITIVE_TEXT_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|apikey|access[_-]?key|secret|token|password|"
               r"passwd|credential|private[_-]?key|client[_-]?secret)\s*[:=]"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
]
SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"(?i)\.env$"),
    re.compile(r"(?i)\.pem$"),
    re.compile(r"(?i)\.key$"),
    re.compile(r"(?i)\.p12$"),
    re.compile(r"(?i)\.pfx$"),
    re.compile(r"(?i)\.crt$"),
    re.compile(r"(?i)(^|/)(id_rsa|id_ed25519|id_ecdsa|id_dsa)(\.|$)"),
    re.compile(r"(?i)(^|/)credentials\.json$"),
]
SAFE_FILENAME = re.compile(r"(?i)\.env\.example$")

LOCK_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "cargo.lock", "go.sum", "pipfile.lock", "composer.lock",
}
DEP_FILES = {
    "package.json", "go.mod", "pyproject.toml", "setup.py", "setup.cfg",
    "cargo.toml", "pipfile", "environment.yml", "requirements.txt",
}
CODE_EXT = (
    ".py", ".c", ".cpp", ".cc", ".h", ".hpp", ".v", ".sv", ".go", ".js",
    ".jsx", ".ts", ".tsx", ".lua", ".sh", ".ps1", ".rs", ".java", ".rb", ".svh",
)
DOC_EXT = (".md", ".rst", ".txt")
CONFIG_EXT = (".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".json", ".env")


def run_git(args, cwd):
    try:
        proc = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except FileNotFoundError:
        return None, "git-not-found"
    return proc.stdout, None


def classify(path):
    p = path.lower()
    base = os.path.basename(p)
    segs = p.split("/")
    if any(s in segs for s in ("dist", "build", "node_modules", ".cache",
                               "generated", "out", "__pycache__")):
        return "generated"
    if base in LOCK_FILES or base.endswith(".lock"):
        return "dependency"
    if base.endswith(DOC_EXT) or "docs/" in segs or base.startswith("readme") \
            or base.startswith("doc"):
        return "docs"
    if ("/test" in p or "/tests" in p or "/__tests__" in p
            or base.startswith("test_") or base.endswith("_test.py")
            or ".test." in p or base.endswith("_spec.rb")):
        return "test"
    if base.endswith(CONFIG_EXT):
        if base in DEP_FILES:
            return "dependency"
        return "config"
    if base.endswith(CODE_EXT):
        return "code"
    return "other"


def detect_split_signals(cats, staged):
    """Return the subset of split signals detectable from filenames.

    The agent additionally applies the semantic signals (feature+fix,
    formatting+logic) by reading the diff, per references/split-criteria.md.
    """
    signals = []
    has = lambda k: cats.get(k, 0) > 0
    if has("code") and has("docs"):
        signals.append("代码逻辑 + 文档大改")
    if has("code") and has("dependency"):
        signals.append("依赖升级 + 功能修改")
    tops = {f.split("/", 1)[0] for f in staged if "/" in f}
    if len(tops) >= 3:
        signals.append("多个互不相关模块 (%d 个顶层目录)" % len(tops))
    return signals


def analyze(cwd):
    cwd = os.path.abspath(cwd)
    res = {
        "repo_valid": False,
        "branch": None,
        "protected_branch": False,
        "staging_empty": True,
        "staged_count": 0,
        "staged_files": [],
        "total_added": 0,
        "total_deleted": 0,
        "binary_files": [],
        "categories": {},
        "big_diff": False,
        "sensitive_hits": [],
        "split_signals": [],
        "name_status": [],
        "notes": [],
    }

    inside, err = run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    if err or (inside is not None and inside.strip() != "true"):
        res["notes"].append("not a git repository (rev-parse failed)")
        return res
    res["repo_valid"] = True

    branch, _ = run_git(["branch", "--show-current"], cwd)
    branch = (branch or "").strip()
    res["branch"] = branch
    res["protected_branch"] = branch in PROTECTED_BRANCHES

    status, _ = run_git(["status", "--short"], cwd)
    unstaged = [l for l in (status or "").splitlines()
                if l and l[0] in (" ", "?")]
    if unstaged:
        res["notes"].append(
            "%d unstaged/untracked file(s) NOT included in this commit analysis"
            % len(unstaged))

    names_out, _ = run_git(["diff", "--cached", "--name-only"], cwd)
    staged = [l for l in (names_out or "").splitlines() if l.strip()]
    res["staged_files"] = staged
    res["staged_count"] = len(staged)
    res["staging_empty"] = len(staged) == 0
    if res["staging_empty"]:
        res["notes"].append("staging area empty -> stop, do not commit")
        return res

    numstat_out, _ = run_git(["diff", "--cached", "--numstat"], cwd)
    total_added = total_deleted = 0
    for line in (numstat_out or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, d = parts[0], parts[1]
        if a == "-" and d == "-":
            res["binary_files"].append(parts[2])
            continue
        try:
            total_added += int(a)
        except ValueError:
            pass
        try:
            total_deleted += int(d)
        except ValueError:
            pass
    res["total_added"] = total_added
    res["total_deleted"] = total_deleted

    ns_out, _ = run_git(["diff", "--cached", "--name-status"], cwd)
    res["name_status"] = [l.split("\t")[0] for l in (ns_out or "").splitlines() if l]

    cats = {}
    for f in staged:
        c = classify(f)
        cats[c] = cats.get(c, 0) + 1
    res["categories"] = cats

    res["big_diff"] = (res["staged_count"] > BIG_FILE_THRESHOLD
                       or (total_added + total_deleted) > BIG_LINE_THRESHOLD)
    if res["big_diff"]:
        res["notes"].append("large diff -> use --stat/--name-status, suggest split")

    for f in staged:
        for pat in SENSITIVE_FILENAME_PATTERNS:
            if pat.search(f) and not SAFE_FILENAME.search(f):
                res["sensitive_hits"].append({"file": f, "pattern": pat.pattern})
                break
    diff_text, _ = run_git(["diff", "--cached"], cwd)
    if diff_text:
        if len(diff_text) > DIFF_SCAN_CAP:
            diff_text = diff_text[:DIFF_SCAN_CAP]
        for pat in SENSITIVE_TEXT_PATTERNS:
            m = pat.search(diff_text)
            if m:
                res["sensitive_hits"].append(
                    {"file": "<diff-text>", "pattern": pat.pattern,
                     "match": m.group(0)[:40]})
                break
    if res["sensitive_hits"]:
        res["notes"].append("SENSITIVE HIT -> stop commit, warn user")

    res["split_signals"] = detect_split_signals(cats, staged)
    if res["split_signals"]:
        res["notes"].append("split suggested -> generate per-group messages")

    return res


def render_text(res):
    lines = ["=== smart-commit staged analysis ===",
             "repo_valid:       %s" % res["repo_valid"]]
    if res["repo_valid"]:
        lines.append("branch:           %s%s" % (
            res["branch"], "  [PROTECTED]" if res["protected_branch"] else ""))
        lines.append("staging_empty:    %s" % res["staging_empty"])
        lines.append("staged_count:     %d" % res["staged_count"])
        lines.append("added/deleted:    %d / %d" % (res["total_added"], res["total_deleted"]))
        lines.append("binary_files:     %s" % (res["binary_files"] or "[]"))
        lines.append("categories:       %s" % res["categories"])
        lines.append("big_diff:         %s" % res["big_diff"])
        lines.append("sensitive_hits:   %s" % (res["sensitive_hits"] or "[]"))
        lines.append("split_signals:    %s" % (res["split_signals"] or "[]"))
        lines.append("name_status:      %s" % (res["name_status"] or "[]"))
    if res["notes"]:
        lines.append("--- notes ---")
        lines.extend(" - " + n for n in res["notes"])
    return "\n".join(lines)


def main(argv):
    repo = os.getcwd()
    as_json = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--repo" and i + 1 < len(argv):
            repo = argv[i + 1]
            i += 2
            continue
        if a == "--json":
            as_json = True
            i += 1
            continue
        i += 1
    repo = os.path.abspath(repo)
    if not os.path.isdir(repo):
        print("smart-commit: repo path not found: %s" % repo)
        sys.exit(2)
    res = analyze(repo)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_text(res))
        print()
        print("```json")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print("```")


if __name__ == "__main__":
    main(sys.argv[1:])
