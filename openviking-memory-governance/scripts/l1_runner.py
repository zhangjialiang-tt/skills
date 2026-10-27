#!/usr/bin/env python3
"""L1 batch: strip ChatLog sections from all OpenViking event files.

Per file: keep verbatim head (Summary) + original MEMORY_FIELDS block,
write via ov write to an underscore temp URI, then ov mv onto the real URI.
Idempotent: files without a ChatLog section are skipped.
Progress: /app/.openviking/backup/events-prune-20261026/l1-progress.jsonl
Done marker: .../l1-DONE (json summary)
"""
import json, os, re, subprocess, sys, time

BASE = "/app/.openviking/workspace/viking/default/user/zhangjl"
WORK = "/app/.openviking/backup/events-prune-20261026"
PROGRESS = os.path.join(WORK, "l1-progress.jsonl")
DONE = os.path.join(WORK, "l1-DONE")
TMPDIR = "/tmp/l1work"
os.makedirs(TMPDIR, exist_ok=True)

CHATLOG_RE = re.compile(r"^# [^\n]*ChatLog:", flags=re.M)
FIELDS_RE = re.compile(r"<!-- MEMORY_FIELDS.*?-->", flags=re.S)

def strip_content(txt):
    m = CHATLOG_RE.search(txt)
    if not m:
        return None
    head = txt[: m.start()].rstrip()
    fm = FIELDS_RE.search(txt)
    out = head + ("\n\n" + fm.group(0) + "\n" if fm else "\n")
    return out

def run_ov(args, timeout=180):
    r = subprocess.run(["ov"] + args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def disk_to_uri(path):
    rel = os.path.relpath(path, "/app/.openviking/workspace/viking/default")
    return "viking://" + rel

def process_file(path, log):
    rel = os.path.relpath(path, BASE)
    try:
        raw = open(path, "rb").read()
        txt = raw.decode("utf-8")
    except Exception as e:
        log({"rel": rel, "status": "read-error", "err": str(e)[:200]})
        return
    stripped = strip_content(txt)
    if stripped is None:
        return  # no chatlog: skip silently (already clean)
    before = len(raw)
    uri = disk_to_uri(path)
    dirname, fname = uri.rsplit("/", 1)
    tmp_name = fname.replace(" ", "_")
    tmp_uri = dirname + "/" + tmp_name
    tmp_disk = os.path.join(os.path.dirname(path), tmp_name)
    if tmp_uri != uri and os.path.exists(tmp_disk):
        log({"rel": rel, "status": "collision-skip", "before": before})
        return
    tmp_content = os.path.join(TMPDIR, "cur.md")
    with open(tmp_content, "w", encoding="utf-8") as fh:
        fh.write(stripped)
    try:
        if tmp_uri == uri:
            rc, out = run_ov(["write", uri, "--from-file", tmp_content, "--wait"])
            if rc != 0:
                raise RuntimeError("write rc=%d %s" % (rc, out[-200:]))
        else:
            rc, out = run_ov(["write", tmp_uri, "--from-file", tmp_content, "--wait"])
            if rc != 0:
                raise RuntimeError("write rc=%d %s" % (rc, out[-200:]))
            rc, out = run_ov(["mv", tmp_uri, uri])
            if rc != 0:
                raise RuntimeError("mv rc=%d %s" % (rc, out[-200:]))
    except Exception as e:
        log({"rel": rel, "status": "fail", "before": before, "err": str(e)[:300]})
        return
    # verify on disk
    try:
        new_raw = open(path, "rb").read()
        new_txt = new_raw.decode("utf-8")
        ok = ("ChatLog:" not in new_txt)
        log({"rel": rel, "status": "ok" if ok else "verify-suspect",
             "before": before, "after": len(new_raw)})
    except Exception as e:
        log({"rel": rel, "status": "verify-error", "before": before, "err": str(e)[:200]})

def main():
    roots = []
    user_events = os.path.join(BASE, "memories/events")
    if os.path.isdir(user_events):
        roots.append(("user", user_events))
    peers_dir = os.path.join(BASE, "peers")
    for peer in sorted(os.listdir(peers_dir)):
        ev = os.path.join(peers_dir, peer, "memories/events")
        if os.path.isdir(ev):
            roots.append((peer, ev))
    # small scopes first, big three last
    def scope_size(item):
        n = 0
        for dp, dn, fn in os.walk(item[1]):
            n += sum(1 for f in fn if f.endswith(".md") and not f.startswith("."))
        return n
    roots.sort(key=scope_size)
    started = time.time()
    counts = {"ok": 0, "fail": 0, "collision-skip": 0, "verify-suspect": 0,
              "read-error": 0, "verify-error": 0}
    bytes_before = bytes_after = 0
    with open(PROGRESS, "a", encoding="utf-8") as pf:
        def log(rec):
            rec["t"] = round(time.time() - started, 1)
            pf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            pf.flush()
            st = rec.get("status")
            if st in counts:
                counts[st] += 1
        for name, root in roots:
            log({"scope": name, "status": "scope-start"})
            for dp, dn, fn in os.walk(root):
                for f in sorted(fn):
                    if f.endswith(".md") and not f.startswith("."):
                        p = os.path.join(dp, f)
                        pre = counts["ok"]
                        process_file(p, log)
                        if counts["ok"] > pre:
                            pass
            log({"scope": name, "status": "scope-done", "counts": dict(counts)})
    # byte totals from progress log
    for line in open(PROGRESS, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("status") == "ok":
            bytes_before += r.get("before", 0)
            bytes_after += r.get("after", 0)
    summary = {"counts": counts, "bytes_before": bytes_before,
               "bytes_after": bytes_after,
               "elapsed_s": round(time.time() - started, 1)}
    with open(DONE, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("DONE", summary)

if __name__ == "__main__":
    main()
