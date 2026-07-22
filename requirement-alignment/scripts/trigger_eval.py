#!/usr/bin/env python3
"""
Trigger Eval — requirement-alignment 路由回归测试

用法：
    python3 scripts/trigger_eval.py

功能：
    - 读取 evals/evals.json 中的测试用例
    - 对每个用例判断是否应触发本 Skill
    - 输出命中率、精确率、召回率
"""

import json
import os
import sys
from pathlib import Path

# 项目根目录
SKILL_DIR = Path(__file__).resolve().parent.parent
EVALS_FILE = SKILL_DIR / "evals" / "evals.json"


def load_evals() -> list[dict]:
    """加载测试用例"""
    if not EVALS_FILE.exists():
        print(f"❌ 评测文件不存在: {EVALS_FILE}")
        sys.exit(1)
    with open(EVALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("evals", [])


def check_trigger(prompt: str) -> bool:
    """
    模拟触发判断逻辑。
    
    实际实现中，这里应该：
    1. 调用模型判断 prompt 是否应触发
    2. 返回 True/False
    
    当前为占位实现：基于关键词的简单规则。
    """
    # 触发关键词（与 frontmatter triggers 对齐）
    trigger_keywords = [
        "优化", "重构", "支持", "先确认", "先不要写代码",
        "帮我梳理", "歧义", "多种理解", "不确定",
        "既要", "又要", "还要", "大范围", "删除", "迁移",
        "边界不清", "验收", "目标不明", "手段"
    ]
    
    # 排除关键词
    exclude_keywords = [
        "把", "改为", "运行", "解释", "说明", "查询",
        "格式化", "注释", "重命名"
    ]
    
    has_trigger = any(kw in prompt for kw in trigger_keywords)
    has_exclude = any(kw in prompt for kw in exclude_keywords)
    
    # 简单启发式：有触发词且无排除词
    return has_trigger and not has_exclude


def run_eval():
    """运行评测"""
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
    
    # 输出结果
    print("=" * 60)
    print(f"Trigger Eval — requirement-alignment")
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
    
    # 返回退出码
    if correct == total:
        print("🎉 全部通过！")
        sys.exit(0)
    else:
        print(f"⚠️ {total - correct} 个用例未通过")
        sys.exit(1)


if __name__ == "__main__":
    run_eval()
