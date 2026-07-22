#!/usr/bin/env python3
"""
Trigger Eval — ai-plat-bridge 路由回归测试

用法：
    python3 scripts/trigger_eval.py

功能：
    - 读取 evals/evals.json 中的测试用例
    - 对每个用例判断是否应触发本 Skill
    - 输出命中率、精确率、召回率
"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
EVALS_FILE = SKILL_DIR / "evals" / "evals.json"


def load_evals() -> list[dict]:
    if not EVALS_FILE.exists():
        print(f"❌ 评测文件不存在: {EVALS_FILE}")
        sys.exit(1)
    with open(EVALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("evals", [])


def check_trigger(prompt: str) -> bool:
    """
    模拟触发判断逻辑。
    当前为占位实现：基于关键词的简单规则。
    """
    trigger_keywords = [
        "记录到工作台", "查工作台", "查项目状态", "查今日日志",
        "工作台同步", "更新项目文件", "写工作日志", "更新项目记忆",
        "看今天干了什么", "同步进展", "工作台"
    ]
    exclude_keywords = [
        "查一下", "帮我查", "解释", "说明", "查询", "看一下"
    ]
    
    has_trigger = any(kw in prompt for kw in trigger_keywords)
    has_exclude = any(kw in prompt for kw in exclude_keywords)
    
    return has_trigger and not has_exclude


def run_eval():
    evals = load_evals()
    if not evals:
        print("⚠️ 无测试用例")
        return
    
    total = len(evals)
    correct = 0
    results = []
    
    for case in evals:
        prompt = case.get("prompt", "")
        should_trigger = case.get("should_trigger", False)
        case_id = case.get("id", "?")
        
        predicted = check_trigger(prompt)
        is_correct = predicted == should_trigger
        
        if is_correct:
            correct += 1
        
        results.append({
            "id": case_id,
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "should_trigger": should_trigger,
            "predicted": predicted,
            "correct": is_correct
        })
    
    print("=" * 60)
    print(f"Trigger Eval — ai-plat-bridge")
    print("=" * 60)
    print(f"总用例数: {total}")
    print(f"正确数: {correct}")
    print(f"准确率: {correct/total*100:.1f}%")
    print("-" * 60)
    
    for r in results:
        status = "✅" if r["correct"] else "❌"
        trigger_str = "触发" if r["should_trigger"] else "不触发"
        print(f"  {status} #{r['id']}: {trigger_str} | {r['prompt']}")
    
    print("=" * 60)
    
    if correct == total:
        print("🎉 全部通过！")
        sys.exit(0)
    else:
        print(f"⚠️ {total - correct} 个用例未通过")
        sys.exit(1)


if __name__ == "__main__":
    run_eval()
