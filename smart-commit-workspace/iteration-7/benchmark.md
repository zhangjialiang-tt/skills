# Skill Benchmark: smart-commit

**Date**: 2026-10-30T18:18:50Z
**Evals**: 暂存区为空应如实报告, 生成 message 不执行 commit 且格式合规, 明确要求执行提交时才 commit (1 runs each per configuration)

## Summary

| Metric | With Skill |
|--------|------------|
| Pass Rate | 83% ± 24% |

## Per-Case Results

### 暂存区为空应如实报告 (with_skill)

- **Pass Rate**: 100% (1/1)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.cmd | ✅ | ALL PASS: git 状态判定通过 |

### 生成 message 不执行 commit 且格式合规 (with_skill)

- **Pass Rate**: 50% (1/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_not_contain | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.cmd | ❌ | script exited with code 1 [stderr: Traceback (most recent call last):
  File "C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.py", line 73, in <module>
    sys.exit(main())
             ^^^^^^
  File "C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.py", line 52, in main
    check(bool(re.search(r"(feat|fix|docs|chore|refactor)\b.*\p{Emoji}|\p{Emoji}.*\p{Emoji}", final, re.I)),
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\__init__.py", line 176, in search
    return _compile(pattern, flags).search(string)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\__init__.py", line 294, in _compile
    p = _compiler.compile(pattern, flags)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\_compiler.py", line 743, in compile
    p = _parser.parse(p, flags)
        ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\_parser.py", line 980, in parse
    p = _parse_sub(source, state, flags & SRE_FLAG_VERBOSE, 0)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\_parser.py", line 455, in _parse_sub
    itemsappend(_parse(source, state, verbose, nested + 1,
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\_parser.py", line 539, in _parse
    code = _escape(source, this, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Software\Python\Python311\Lib\re\_parser.py", line 438, in _escape
    raise source.error("bad escape %s" % escape, len(escape))
re.error: bad escape \p at position 34] |

### 明确要求执行提交时才 commit (with_skill)

- **Pass Rate**: 100% (2/2)

| Expectation | Result | Evidence |
|-------------|--------|----------|
| expect.must_contain | ✅ | all checks passed |
| script: C:\Users\zhangjl\AppData\Local\Temp\zhangjl-skills-eval-sandbox\smart-commit\evals\fixtures\scripts\check_git_state.cmd | ✅ | ALL PASS: git 状态判定通过 |

