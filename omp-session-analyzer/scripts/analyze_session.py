#!/usr/bin/env python3
"""
OMP Session Analyzer - 解析 OMP Agent session JSONL 并生成交互式 HTML 报告
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import html


def parse_args():
    parser = argparse.ArgumentParser(description="OMP Session Analyzer")
    parser.add_argument("input", help="JSONL 文件或 session 目录")
    parser.add_argument("-o", "--output", help="输出 HTML 路径", default=None)
    return parser.parse_args()


def load_jsonl(filepath):
    """加载 JSONL 文件，返回事件列表"""
    events = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def load_sessions_from_dir(dirpath):
    """从目录加载所有 session 文件"""
    all_events = []
    session_files = sorted(Path(dirpath).glob("*.jsonl"))
    for f in session_files:
        events = load_jsonl(f)
        # 标记来源文件
        for e in events:
            e["_source"] = str(f)
        all_events.extend(events)
    return all_events, [str(f) for f in session_files]


def load_all_sessions(base_dir):
    """从基础目录递归加载所有 session"""
    all_events = []
    session_files = sorted(Path(base_dir).rglob("*.jsonl"))
    for f in session_files:
        events = load_jsonl(f)
        for e in events:
            e["_source"] = str(f)
        all_events.extend(events)
    return all_events, [str(f) for f in session_files]


def extract_session_info(events):
    """提取 session 元信息"""
    sessions = {}
    for e in events:
        if e.get("type") == "session":
            sid = e.get("id", "unknown")
            sessions[sid] = {
                "id": sid,
                "timestamp": e.get("timestamp", ""),
                "cwd": e.get("cwd", ""),
                "title": e.get("title", "Untitled"),
                "source": e.get("_source", ""),
            }
    return sessions


def analyze_events(events):
    """分析所有事件，提取指标"""
    sessions = extract_session_info(events)
    
    # 按 session 分组
    session_events = defaultdict(list)
    for e in events:
        # 尝试从 session 事件获取 id，否则从 _source 推断
        sid = None
        if e.get("type") == "session":
            sid = e.get("id")
        elif "_source" in e:
            # 从文件路径推断 session id
            src = e["_source"]
            # 提取文件名（不含扩展名）作为 session id
            fname = Path(src).stem
            for s in sessions:
                if s in fname:
                    sid = s
                    break
        if not sid:
            sid = "_unassigned"
        session_events[sid].append(e)
    
    # 分析每个 session
    session_stats = {}
    for sid, sevs in session_events.items():
        stats = analyze_session_events(sevs)
        if sid in sessions:
            stats["info"] = sessions[sid]
        else:
            stats["info"] = {"id": sid, "title": "Unknown", "timestamp": "", "cwd": ""}
        session_stats[sid] = stats
    
    return session_stats


def analyze_session_events(events):
    """分析单个 session 的事件"""
    stats = {
        "turns": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cache_read": 0,
        "total_cache_write": 0,
        "total_cost": 0.0,
        "total_reasoning_tokens": 0,
        "tool_calls": defaultdict(lambda: {"count": 0, "total_tokens": 0, "total_duration": 0}),
        "models_used": set(),
        "total_duration": 0,
        "user_messages": 0,
        "assistant_messages": 0,
        "tool_results": 0,
        "thinking_blocks": 0,
        "start_time": None,
        "end_time": None,
    }
    
    for e in events:
        timestamp = e.get("timestamp", "")
        if timestamp:
            if not stats["start_time"] or timestamp < stats["start_time"]:
                stats["start_time"] = timestamp
            if not stats["end_time"] or timestamp > stats["end_time"]:
                stats["end_time"] = timestamp
        
        etype = e.get("type", "")
        
        if etype == "message":
            msg = e.get("message", {})
            role = msg.get("role", "")
            
            if role == "user":
                stats["user_messages"] += 1
            elif role == "assistant":
                stats["assistant_messages"] += 1
                # 提取 usage
                usage = msg.get("usage", {})
                if usage:
                    stats["total_input_tokens"] += usage.get("input", 0)
                    stats["total_output_tokens"] += usage.get("output", 0)
                    stats["total_cache_read"] += usage.get("cacheRead", 0)
                    stats["total_cache_write"] += usage.get("cacheWrite", 0)
                    stats["total_reasoning_tokens"] += usage.get("reasoningTokens", 0)
                    cost = usage.get("cost", {})
                    if cost:
                        stats["total_cost"] += cost.get("total", 0)
                
                # 提取模型
                model = msg.get("model", "")
                if model:
                    stats["models_used"].add(model)
                
                # 提取 duration
                duration = msg.get("duration", 0)
                if duration:
                    stats["total_duration"] += duration / 1000  # ms -> s
                
                # 分析 content
                content = msg.get("content", [])
                if isinstance(content, list):
                    turn = {"role": role, "timestamp": timestamp, "tools": [], "thinking": "", "text": ""}
                    for c in content:
                        ctype = c.get("type", "")
                        if ctype == "toolCall":
                            stats["tool_calls"][c.get("name", "unknown")]["count"] += 1
                            turn["tools"].append({
                                "name": c.get("name", ""),
                                "arguments": c.get("arguments", {}),
                                "id": c.get("id", ""),
                            })
                        elif ctype == "thinking":
                            stats["thinking_blocks"] += 1
                            turn["thinking"] = c.get("thinking", "")
                        elif ctype == "text":
                            turn["text"] = c.get("text", "")
                    
                    if turn["tools"] or turn["thinking"] or turn["text"]:
                        stats["turns"].append(turn)
                
            elif role == "toolResult":
                stats["tool_results"] += 1
    
    stats["models_used"] = list(stats["models_used"])
    stats["total_tokens"] = stats["total_input_tokens"] + stats["total_output_tokens"]
    
    return stats


def generate_html(session_stats, output_path):
    """生成 HTML 报告"""
    
    # 汇总统计
    total_sessions = len(session_stats)
    total_tokens = sum(s["total_tokens"] for s in session_stats.values())
    total_input = sum(s["total_input_tokens"] for s in session_stats.values())
    total_output = sum(s["total_output_tokens"] for s in session_stats.values())
    total_cost = sum(s["total_cost"] for s in session_stats.values())
    total_duration = sum(s["total_duration"] for s in session_stats.values())
    total_tool_calls = sum(
        sum(t["count"] for t in s["tool_calls"].values())
        for s in session_stats.values()
    )
    total_thinking = sum(s["thinking_blocks"] for s in session_stats.values())
    
    # 所有模型
    all_models = set()
    for s in session_stats.values():
        all_models.update(s["models_used"])
    
    # 工具调用汇总
    all_tools = defaultdict(lambda: {"count": 0, "total_tokens": 0})
    for s in session_stats.values():
        for tool_name, tool_stats in s["tool_calls"].items():
            all_tools[tool_name]["count"] += tool_stats["count"]
            all_tools[tool_name]["total_tokens"] += tool_stats["total_tokens"]
    
    # 按调用次数排序
    sorted_tools = sorted(all_tools.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # 准备 session 表格数据
    session_rows = []
    for sid, stats in session_stats.items():
        info = stats["info"]
        title = info.get("title", "Untitled")
        ts = info.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        tool_count = sum(t["count"] for t in stats["tool_calls"].values())
        session_rows.append({
            "id": sid[:12] + "...",
            "title": title,
            "timestamp": ts,
            "tokens": stats["total_tokens"],
            "input": stats["total_input_tokens"],
            "output": stats["total_output_tokens"],
            "cost": stats["total_cost"],
            "duration": f"{stats['total_duration']:.1f}s",
            "tools": tool_count,
            "thinking": stats["thinking_blocks"],
            "models": ", ".join(stats["models_used"][:2]),
        })
    
    # 按时间排序
    session_rows.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # 生成工具调用图表数据
    tool_chart_labels = [t[0] for t in sorted_tools[:15]]
    tool_chart_data = [t[1]["count"] for t in sorted_tools[:15]]
    
    # 生成 token 趋势数据（按 session）
    token_timeline = []
    for sid, stats in session_stats.items():
        info = stats["info"]
        ts = info.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                label = dt.strftime("%m-%d %H:%M")
            except:
                label = sid[:8]
        else:
            label = sid[:8]
        token_timeline.append({
            "label": label,
            "input": stats["total_input_tokens"],
            "output": stats["total_output_tokens"],
            "cost": stats["total_cost"],
        })
    token_timeline.sort(key=lambda x: x["label"])
    
    # 生成对话详情
    conversation_html = generate_conversation_html(session_stats)
    
    # 构建 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMP Session Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #58a6ff; margin-bottom: 8px; font-size: 1.8em; }}
        h2 {{ color: #79c0ff; margin: 24px 0 12px; font-size: 1.3em; border-bottom: 1px solid #21262d; padding-bottom: 8px; }}
        h3 {{ color: #a5d6ff; margin: 16px 0 8px; font-size: 1.1em; }}
        .subtitle {{ color: #8b949e; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }}
        .stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
        .stat-value {{ font-size: 1.8em; font-weight: bold; color: #58a6ff; }}
        .stat-label {{ font-size: 0.85em; color: #8b949e; margin-top: 4px; }}
        .chart-container {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
        .chart {{ width: 100%; height: 350px; }}
        table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #21262d; }}
        th {{ background: #1c2128; color: #79c0ff; font-weight: 600; }}
        tr:hover {{ background: #1c2128; }}
        .conversation {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-top: 16px; max-height: 600px; overflow-y: auto; }}
        .turn {{ border-left: 3px solid #30363d; padding: 8px 12px; margin: 8px 0; }}
        .turn.user {{ border-left-color: #1f6feb; }}
        .turn.assistant {{ border-left-color: #238636; }}
        .turn-header {{ font-size: 0.85em; color: #8b949e; margin-bottom: 4px; }}
        .turn-content {{ font-size: 0.9em; white-space: pre-wrap; word-break: break-word; }}
        .tool-call {{ background: #0d1117; border: 1px solid #30363d; border-radius: 4px; padding: 6px 10px; margin: 4px 0; font-size: 0.85em; }}
        .tool-name {{ color: #d2a8ff; font-weight: 600; }}
        .thinking {{ background: #1c2128; border-radius: 4px; padding: 8px; margin: 4px 0; font-size: 0.85em; color: #8b949e; max-height: 200px; overflow-y: auto; }}
        .collapsible {{ cursor: pointer; }}
        .collapsible:hover {{ text-decoration: underline; }}
        .collapsed {{ display: none; }}
        .tag {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; margin-right: 4px; }}
        .tag-blue {{ background: #1f6feb33; color: #58a6ff; }}
        .tag-green {{ background: #23863633; color: #3fb950; }}
        .tag-purple {{ background: #8957e533; color: #d2a8ff; }}
        .filters {{ margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }}
        .filter-btn {{ padding: 6px 14px; border: 1px solid #30363d; background: #161b22; color: #c9d1d9; border-radius: 6px; cursor: pointer; font-size: 0.85em; }}
        .filter-btn:hover, .filter-btn.active {{ background: #1f6feb; border-color: #1f6feb; color: white; }}
        .search-box {{ padding: 6px 12px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; border-radius: 6px; font-size: 0.85em; width: 240px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐲 OMP Session Analysis Report</h1>
        <p class="subtitle">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Sessions: {total_sessions}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_sessions}</div>
                <div class="stat-label">Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_number(total_tokens)}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_number(total_input)}</div>
                <div class="stat-label">Input Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_number(total_output)}</div>
                <div class="stat-label">Output Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${total_cost:.4f}</div>
                <div class="stat-label">Total Cost</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_tool_calls}</div>
                <div class="stat-label">Tool Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_thinking}</div>
                <div class="stat-label">Thinking Blocks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_duration(total_duration)}</div>
                <div class="stat-label">Total Duration</div>
            </div>
        </div>
        
        <h2>📊 Token Usage by Session</h2>
        <div class="chart-container">
            <div id="tokenChart" class="chart"></div>
        </div>
        
        <h2>🔧 Tool Call Distribution</h2>
        <div class="chart-container">
            <div id="toolChart" class="chart"></div>
        </div>
        
        <h2>📋 Session Details</h2>
        <div class="filters">
            <input type="text" class="search-box" id="searchInput" placeholder="Search sessions..." oninput="filterSessions()">
        </div>
        <table id="sessionTable">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Time</th>
                    <th>Tokens</th>
                    <th>Input</th>
                    <th>Output</th>
                    <th>Cost</th>
                    <th>Duration</th>
                    <th>Tools</th>
                    <th>Thinking</th>
                    <th>Models</th>
                </tr>
            </thead>
            <tbody>
                {generate_session_rows(session_rows)}
            </tbody>
        </table>
        
        <h2>💬 Conversation Details</h2>
        <div class="filters">
            <button class="filter-btn active" onclick="filterTurns('all')">All</button>
            <button class="filter-btn" onclick="filterTurns('user')">User</button>
            <button class="filter-btn" onclick="filterTurns('assistant')">Assistant</button>
            <button class="filter-btn" onclick="filterTurns('tool')">With Tools</button>
            <button class="filter-btn" onclick="filterTurns('thinking')">With Thinking</button>
        </div>
        <div class="conversation" id="conversation">
            {conversation_html}
        </div>
    </div>
    
    <script>
        // Token chart
        const tokenChart = echarts.init(document.getElementById('tokenChart'));
        tokenChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            legend: {{ data: ['Input', 'Output'], textStyle: {{ color: '#8b949e' }} }},
            grid: {{ left: '3%', right: '4%', bottom: '3%', containLabel: true }},
            xAxis: {{
                type: 'category',
                data: {json.dumps([t['label'] for t in token_timeline])},
                axisLabel: {{ color: '#8b949e', rotate: 45 }},
                axisLine: {{ lineStyle: {{ color: '#30363d' }} }}
            }},
            yAxis: {{
                type: 'value',
                axisLabel: {{ color: '#8b949e' }},
                splitLine: {{ lineStyle: {{ color: '#21262d' }} }}
            }},
            series: [
                {{
                    name: 'Input',
                    type: 'bar',
                    stack: 'total',
                    data: {json.dumps([t['input'] for t in token_timeline])},
                    itemStyle: {{ color: '#1f6feb' }}
                }},
                {{
                    name: 'Output',
                    type: 'bar',
                    stack: 'total',
                    data: {json.dumps([t['output'] for t in token_timeline])},
                    itemStyle: {{ color: '#238636' }}
                }}
            ]
        }});
        
        // Tool chart
        const toolChart = echarts.init(document.getElementById('toolChart'));
        toolChart.setOption({{
            tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
            grid: {{ left: '3%', right: '4%', bottom: '3%', containLabel: true }},
            xAxis: {{
                type: 'value',
                axisLabel: {{ color: '#8b949e' }},
                splitLine: {{ lineStyle: {{ color: '#21262d' }} }}
            }},
            yAxis: {{
                type: 'category',
                data: {json.dumps(tool_chart_labels[::-1])},
                axisLabel: {{ color: '#8b949e' }},
                axisLine: {{ lineStyle: {{ color: '#30363d' }} }}
            }},
            series: [{{
                type: 'bar',
                data: {json.dumps(tool_chart_data[::-1])},
                itemStyle: {{ color: '#8957e5' }}
            }}]
        }});
        
        window.addEventListener('resize', () => {{
            tokenChart.resize();
            toolChart.resize();
        }});
        
        // Filter functions
        function filterSessions() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const rows = document.querySelectorAll('#sessionTable tbody tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            }});
        }}
        
        function filterTurns(type) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            
            const turns = document.querySelectorAll('.turn');
            turns.forEach(turn => {{
                if (type === 'all') {{
                    turn.style.display = '';
                }} else if (type === 'user') {{
                    turn.style.display = turn.classList.contains('user') ? '' : 'none';
                }} else if (type === 'assistant') {{
                    turn.style.display = turn.classList.contains('assistant') ? '' : 'none';
                }} else if (type === 'tool') {{
                    turn.style.display = turn.querySelector('.tool-call') ? '' : 'none';
                }} else if (type === 'thinking') {{
                    turn.style.display = turn.querySelector('.thinking') ? '' : 'none';
                }}
            }});
        }}
        
        // Collapsible thinking
        document.querySelectorAll('.collapsible').forEach(el => {{
            el.addEventListener('click', () => {{
                el.nextElementSibling.classList.toggle('collapsed');
            }});
        }});
    </script>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return output_path


def generate_session_rows(rows):
    """生成 session 表格行 HTML"""
    html_parts = []
    for r in rows:
        title = html.escape(r["title"][:60] + ("..." if len(r["title"]) > 60 else ""))
        html_parts.append(f"""<tr>
            <td title="{html.escape(r['title'])}">{title}</td>
            <td>{r['timestamp']}</td>
            <td>{format_number(r['tokens'])}</td>
            <td>{format_number(r['input'])}</td>
            <td>{format_number(r['output'])}</td>
            <td>${r['cost']:.4f}</td>
            <td>{r['duration']}</td>
            <td>{r['tools']}</td>
            <td>{r['thinking']}</td>
            <td>{html.escape(r['models'])}</td>
        </tr>""")
    return "\n".join(html_parts)


def generate_conversation_html(session_stats):
    """生成对话详情 HTML"""
    html_parts = []
    
    for sid, stats in session_stats.items():
        info = stats["info"]
        title = html.escape(info.get("title", "Untitled"))
        html_parts.append(f'<h3>📌 {title}</h3>')
        
        for i, turn in enumerate(stats["turns"]):
            role = turn.get("role", "unknown")
            ts = turn.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts = dt.strftime("%H:%M:%S")
                except:
                    pass
            
            css_class = "user" if role == "user" else "assistant"
            html_parts.append(f'<div class="turn {css_class}" data-role="{role}">')
            html_parts.append(f'<div class="turn-header">[{ts}] {role.upper()}</div>')
            
            # Thinking
            thinking = turn.get("thinking", "")
            if thinking:
                thinking_text = html.escape(thinking[:500] + ("..." if len(thinking) > 500 else ""))
                html_parts.append(f'<div class="collapsible" style="color: #8b949e; cursor: pointer;">💭 Thinking ({len(thinking)} chars) ▼</div>')
                html_parts.append(f'<div class="thinking collapsed">{thinking_text}</div>')
            
            # Tool calls
            for tool in turn.get("tools", []):
                tool_name = html.escape(tool.get("name", "unknown"))
                args = tool.get("arguments", {})
                args_str = json.dumps(args, ensure_ascii=False)[:200]
                html_parts.append(f'<div class="tool-call"><span class="tool-name">🔧 {tool_name}</span> <span style="color: #8b949e;">{html.escape(args_str)}</span></div>')
            
            # Text content
            text = turn.get("text", "")
            if text:
                text_escaped = html.escape(text[:1000] + ("..." if len(text) > 1000 else ""))
                html_parts.append(f'<div class="turn-content">{text_escaped}</div>')
            
            html_parts.append('</div>')
    
    return "\n".join(html_parts)


def format_number(n):
    """格式化数字"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def format_duration(seconds):
    """格式化时长"""
    if seconds >= 3600:
        return f"{seconds/3600:.1f}h"
    elif seconds >= 60:
        return f"{seconds/60:.1f}m"
    return f"{seconds:.0f}s"


def main():
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    
    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        sys.exit(1)
    
    # 确定输入类型
    if input_path.is_file():
        print(f"Loading session: {input_path}")
        events = load_jsonl(input_path)
        session_files = [str(input_path)]
    elif input_path.is_dir():
        # 检查是否是 session 目录（包含 JSONL 文件）
        jsonl_files = list(input_path.glob("*.jsonl"))
        if jsonl_files:
            print(f"Loading {len(jsonl_files)} sessions from: {input_path}")
            events, session_files = load_sessions_from_dir(input_path)
        else:
            # 可能是 sessions 根目录
            print(f"Loading all sessions from: {input_path}")
            events, session_files = load_all_sessions(input_path)
    
    print(f"Loaded {len(events)} events from {len(session_files)} files")
    
    # 分析
    print("Analyzing events...")
    session_stats = analyze_events(events)
    print(f"Found {len(session_stats)} sessions")
    
    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"omp_report_{timestamp}.html"
    
    # 生成报告
    print(f"Generating HTML report: {output_path}")
    generate_html(session_stats, output_path)
    
    # 输出摘要
    total_tokens = sum(s["total_tokens"] for s in session_stats.values())
    total_cost = sum(s["total_cost"] for s in session_stats.values())
    print(f"\n{'='*50}")
    print(f"Report saved: {output_path}")
    print(f"Sessions: {len(session_stats)}")
    print(f"Total tokens: {format_number(total_tokens)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
