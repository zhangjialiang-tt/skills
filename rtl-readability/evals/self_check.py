# -*- coding: utf-8 -*-
"""rtl-readability v2.2.0-rebuilt 自检（11 用例，复现 v2.1 self_check 形态）。

运行：python -I evals/self_check.py
exit 0 = 11/11 PASS。
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "scripts", "readability_model.py")

SAMPLE_V = """module counter #(parameter WIDTH = 8) (
  input wire clk,
  input wire rst_n,
  output wire [WIDTH-1:0] count
);
  // valid-ready 握手，ready 由下游给出
  reg [WIDTH-1:0] cnt;
  always @(posedge clk) cnt <= cnt + 1;
  assign count = cnt;
endmodule
"""

SAMPLE_EMPTY = "module t();\nendmodule\n"


def run_model(*argv):
    r = subprocess.run([sys.executable, "-I", MODEL, *argv],
                       capture_output=True, text=True)
    return r


def main():
    results = []

    def case(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    with tempfile.TemporaryDirectory() as d:
        v1 = os.path.join(d, "a.v")
        open(v1, "w", encoding="utf-8").write(SAMPLE_V)
        v2 = os.path.join(d, "b.v")
        open(v2, "w", encoding="utf-8").write(SAMPLE_EMPTY)

        # 1 check 退出码 0
        r = run_model("check", v1, "--sheet", os.path.join(d, "s1.json"))
        case("check-exit-0", r.returncode == 0)
        # 2 sheet JSON 可解析且 14 项
        s1 = json.load(open(os.path.join(d, "s1.json"), encoding="utf-8"))
        case("sheet-14-probes", len(s1["probes"]) == 14, str(len(s1["probes"])))
        # 3 三态计数和为 14
        sc = s1["score"]
        case("score-sum-14", sc["answered"] + sc["implicit"] + sc["undocumented"] == 14)
        # 4 注释命中维度判 answered
        case("comment-hit-answered",
             any(p["status"] == "answered" for p in s1["probes"]))
        # 5 空源码 implicit 为主
        r = run_model("check", v2, "--sheet", s2p := os.path.join(d, "s2.json"))
        s2 = json.load(open(s2p, encoding="utf-8"))
        case("empty-implicit-dominant", s2["score"]["implicit"] >= 10, str(s2["score"]))
        # 6 重复运行幂等
        r2 = run_model("check", v1, "--sheet", s1p2 := os.path.join(d, "s1b.json"))
        s1b = json.load(open(s1p2, encoding="utf-8"))
        case("check-idempotent", s1 == s1b)
        # 7 compare 幂等 diff=0
        r = run_model("compare", "--facts", s1, s1b) if False else run_model("compare", "--facts", os.path.join(d, "s1.json"), s1p2)
        out = json.loads(r.stdout)
        case("compare-idempotent", out["changed"] == 0)
        # 8 compare 检出 status 变化
        s2b = json.loads(json.dumps(s1))
        for p in s2b["probes"]:
            if p["status"] == "implicit":
                p["status"] = "answered"
        s2b_p = os.path.join(d, "s2b.json")
        json.dump(s2b, open(s2b_p, "w", encoding="utf-8"))
        r = run_model("compare", "--facts", os.path.join(d, "s1.json"), s2b_p)
        out = json.loads(r.stdout)
        case("compare-detects", out["changed"] > 0)
        # 9 render 输出六节
        fj = os.path.join(d, "findings.json")
        json.dump({"module": "a", "verdict": "pass", "findings": [],
                   "probes": s1["probes"]}, open(fj, "w", encoding="utf-8"))
        r = run_model("render", fj, "--out", os.path.join(d, "r.md"))
        rep = open(os.path.join(d, "r.md"), encoding="utf-8").read()
        case("render-exit-0", r.returncode == 0)
        case("render-six-sections", all("## %d" % i in rep for i in range(1, 7)))
        # 11 rank 退出码 0
        r = run_model("rank", os.path.join(d, "s1.json"), s2p)
        case("rank-exit-0", r.returncode == 0)

    n_pass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    print("SELF-CHECK %d/%d" % (n_pass, len(results)))
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
