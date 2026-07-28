"""把本次抓取结果和上次的 baseline 做对比，生成人话版变更报告。"""
from __future__ import annotations

import re
from datetime import date as _date

FIELDS = [("input", "输入"), ("cached", "缓存输入"),
          ("output", "输出"), ("context", "上下文")]

# 影子字段：不进表格，只用来发现「源自己改了主意」。分两组，因为该做的事不同。
#
# *_auto —— 你锁定过的字段，源那边报的原值。例如 grok-4.5 的 cached 你锁成
#           0.30、源报 0.50；哪天源修正成 0.30，表格数字不会变（本来就按你的值
#           输出），但 cached_auto 从 0.5 变 0.3 —— 那是「可以撤掉覆盖了」的信号。
# *_or   —— OpenRouter 报的值。主源漏更新时它可能先动，是个早期信号；
#           但也可能只是 OpenRouter 自己在打折，所以两种可能都得说清楚。
SHADOW_AUTO = [("input_auto", "源报输入"), ("cached_auto", "源报缓存输入"),
               ("output_auto", "源报输出"), ("context_auto", "源报上下文")]
SHADOW_XREF = [("input_or", "输入"), ("cached_or", "缓存输入"),
               ("output_or", "输出")]

DEADLINE_WITHIN = 60          # 距下线日期几天内开始提醒


def _fmt(v, field):
    if v is None:
        return "—"
    if field in ("context", "context_auto"):
        return f"{int(v):,}"
    return f"${v:g}"


def _parse_date(v) -> _date | None:
    """从 '2026-10-23' 或 '⚠ 2026-10-23 下线' 里取出日期，取不到返回 None。"""
    if not v:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    if not m:
        return None
    try:
        return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def compare(old: dict, new: dict) -> dict:
    """返回 {added, removed, changed, deprecations, source_moves}"""
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    changed = []
    deprecations = []
    source_moves = []
    xref_moves = []

    for key in new:
        if key not in old:
            continue
        o, n = old[key], new[key]

        deltas = []
        for field, label in FIELDS:
            a, b = o.get(field), n.get(field)
            if a != b:
                pct = ""
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a:
                    pct = f"（{(b - a) / a * 100:+.0f}%）"
                deltas.append(f"{label} {_fmt(a, field)} → {_fmt(b, field)}{pct}")
        if deltas:
            changed.append((key, n.get("name", key), deltas))

        # 影子字段。两边都得有值才比，否则升级后首次运行会凭空报一堆
        for group, bucket in ((SHADOW_AUTO, source_moves), (SHADOW_XREF, xref_moves)):
            shifts = []
            for field, label in group:
                a, b = o.get(field), n.get(field)
                if a is None or b is None or a == b:
                    continue
                shifts.append(f"{label} {_fmt(a, field)} → {_fmt(b, field)}")
            if shifts:
                bucket.append((key, n.get("name", key), shifts))

        if o.get("deprecation_date") != n.get("deprecation_date") and n.get("deprecation_date"):
            deprecations.append((key, n["deprecation_date"]))

    return {"added": added, "removed": removed, "changed": changed,
            "deprecations": deprecations, "source_moves": source_moves,
            "xref_moves": xref_moves}


def deadlines(new: dict, today: str, within: int = DEADLINE_WITHIN) -> tuple[list, list]:
    """扫出「已过下线日期」和「即将到期」两组。

    日期有两个来源，要分开看，因为对应的动作不一样：
      配置 —— models.yaml 的 status 里手写的 '⚠ 2026-10-23 下线'。
               到期了说明该把这行挪进 retired.yaml。
      源   —— 价格源的 deprecation_date（覆盖不全）。它说过期、而你的 status
               没写日期，那是两边对不上，得人去判断谁对。
    写了 expired_ok: true 的跳过——那是你明知过期仍要留在表里的（比如第一方
    退役但 Bedrock / Vertex 还能调）。不给豁免口子，这条会每周告警到永远。
    """
    t = _parse_date(today) or _date.today()
    passed, soon = [], []
    for key, rec in new.items():
        if rec.get("expired_ok"):
            continue
        from_cfg = _parse_date(rec.get("status"))
        from_src = _parse_date(rec.get("deprecation_date"))
        cands = [(d, o) for d, o in ((from_cfg, "配置"), (from_src, "源")) if d]
        if not cands:
            continue
        d, origin = min(cands, key=lambda x: x[0])
        days = (d - t).days
        name = rec.get("name", key)
        if days < 0:
            passed.append((key, name, d.isoformat(), -days, origin))
        elif days <= within:
            soon.append((key, name, d.isoformat(), days, origin))
    passed.sort(key=lambda x: x[2])
    soon.sort(key=lambda x: x[2])
    return passed, soon


def has_changes(d: dict, page_changes: list, alerts: list,
                new_models=(), gone_models=(), passed=()) -> bool:
    """是否有「值得打扰你」的变化 —— CI 靠这个决定要不要开 PR。

    notices（配置锁定值与源不一致、两源分歧）故意不在这里：那些是持续存在
    的已知状态，算进来的话每周都会开一个内容相同的 PR。
    """
    return bool(d["added"] or d["removed"] or d["changed"] or d["deprecations"]
                or d["source_moves"] or d["xref_moves"] or page_changes or alerts
                or new_models or gone_models or passed)


def render(d: dict, new: dict, page_changes: list, alerts: list, notices: list,
           date: str, discovered: dict | None = None, gone: dict | None = None,
           passed: list | None = None, soon: list | None = None,
           groups: dict | None = None, hints: dict | None = None,
           first_snapshot: int | None = None) -> str:
    discovered = discovered or {}
    gone = gone or {}
    passed = passed or []
    soon = soon or []
    groups = groups or {}
    hints = hints or {}

    L = [f"# 模型价格变更报告 · {date}", ""]

    if not has_changes(d, page_changes, alerts, discovered, gone, passed):
        L += ["本次检查未发现需要处理的变化。", ""]
        if notices:
            L += ["## 仅供参考（持续状态，无需处理）", ""]
            L += [f"- {w}" for w in notices]
            L.append("")
        if soon:
            L += _deadline_block(soon)
        if first_snapshot is not None:
            L += [f"> 首次建立未纳管模型快照：记录 {first_snapshot} 条。"
                  f"之后只报相对这份快照新出现的型号。"
                  f"想复核这 {first_snapshot} 条跑 `python run.py --list-unmanaged`。", ""]
        return "\n".join(L)

    if d["changed"]:
        L += ["## 价格 / 参数变动", ""]
        for key, name, deltas in d["changed"]:
            L.append(f"- **{name}** (`{key}`)")
            L += [f"  - {x}" for x in deltas]
        L.append("")

    if discovered:
        L += ["## 价格源出现未纳管的新模型", "",
              "以下型号在源里有价，但 `config/models.yaml` 没登记，"
              "所以**不在表格里**。确认要收录就把对应行粘进 models.yaml：", ""]
        for fam, keys in sorted(groups.items()):
            main = keys[0]
            rec = discovered.get(main, {})
            extra = f"（同族还有 {', '.join(keys[1:])}）" if len(keys) > 1 else ""
            L.append(f"- **{fam}**{extra}：输入 {_fmt(rec.get('input'), 'input')} / "
                     f"缓存 {_fmt(rec.get('cached'), 'cached')} / "
                     f"输出 {_fmt(rec.get('output'), 'output')} / "
                     f"上下文 {_fmt(rec.get('context'), 'context')}")
            if main in hints:
                L += ["", "  ```yaml", f"  {hints[main]}", "  ```"]
        L.append("")

    if gone:
        L += ["## 未纳管条目从价格源消失", "",
              "这些本来就不在表格里，只是顺手告诉你源那边删了：", ""]
        L += [f"- `{k}`" for k in sorted(gone)]
        L.append("")

    if passed:
        L += ["## ⚠ 已过下线日期，仍留在表格里", ""]
        by_cfg = [x for x in passed if x[4] == "配置"]
        by_src = [x for x in passed if x[4] == "源"]
        if by_cfg:
            L += ["你在 `status` 里标的日期已经到了，调用大概已经报错。"
                  "确认后把这几行从 `models.yaml` 挪进 `retired.yaml`：", ""]
            for key, name, day, ago, _ in by_cfg:
                L.append(f"- **{name}** (`{key}`)：{day}，已过 {ago} 天")
            L.append("")
        if by_src:
            L += ["价格源标了下线日期、但你的 `status` 里没写——两边对不上，"
                  "得你判断谁对：", ""]
            for key, name, day, ago, _ in by_src:
                L.append(f"- **{name}** (`{key}`)：源说 {day} 下线（已过 {ago} 天），"
                         f"你标的是「{new.get(key, {}).get('status', '')}」")
            L += ["", "两种处理方式：源是对的 → 挪进 `retired.yaml`；"
                  "源是错的（它对下线日期覆盖得不全，也会写错）→ 在那行加 "
                  "`expired_ok: true` 永久静音。", ""]

    if soon:
        L += _deadline_block(soon)

    if d["added"]:
        L += ["## 受管清单新增（你自己加进 models.yaml 的）", ""]
        for k in d["added"]:
            n = new[k]
            L.append(f"- **{n.get('name', k)}** (`{k}`)："
                     f"输入 {_fmt(n.get('input'), 'input')} / "
                     f"缓存 {_fmt(n.get('cached'), 'cached')} / "
                     f"输出 {_fmt(n.get('output'), 'output')}")
        L.append("")

    if d["removed"]:
        L += ["## 受管清单移除（你自己从 models.yaml 删的）", ""]
        L += [f"- `{k}`" for k in d["removed"]]
        L.append("")

    if d["deprecations"]:
        L += ["## 价格源新标注了下线日期", ""]
        L += [f"- `{k}`：{v}" for k, v in d["deprecations"]]
        L.append("")

    if d["source_moves"]:
        L += ["## 主源改了口径（表格数字未变）", "",
              "这些字段你在 models.yaml 里锁定过，所以表格不受影响。"
              "但主源那边的值动了——如果它已经跟官网一致，覆盖就可以撤掉了：", ""]
        for key, name, shifts in d["source_moves"]:
            L.append(f"- **{name}** (`{key}`)")
            L += [f"  - {x}" for x in shifts]
        L.append("")

    if d["xref_moves"]:
        L += ["## 校验源（OpenRouter）改价了", "",
              "主源还没动。可能是官网真改价了、OpenRouter 先反映出来，"
              "也可能只是它自己在打折——值得核对一眼官网：", ""]
        for key, name, shifts in d["xref_moves"]:
            L.append(f"- **{name}** (`{key}`)")
            L += [f"  - {x}" for x in shifts]
        L.append("")

    if page_changes:
        L += ["## 官方页面内容有变动", "",
              "价格源不一定同步了，建议点开看一眼有没有新的下线公告或分档规则：", ""]
        L += [f"- {u}" for u in page_changes]
        L.append("")

    if alerts:
        L += ["## 需要人工判断", ""]
        L += [f"- {w}" for w in alerts]
        L.append("")

    if notices:
        L += ["## 仅供参考（持续状态，无需处理）", ""]
        L += [f"- {w}" for w in notices]
        L.append("")

    if first_snapshot is not None:
        L += [f"> 首次建立未纳管模型快照：记录 {first_snapshot} 条，本次不逐条列出。"
              f"跑 `python run.py --list-unmanaged` 可复核。", ""]

    L += ["---",
          "确认无误后，把新的 `data/baseline.json` 和 xlsx 合入即可；",
          "如果发现价格源报错，请改 `config/models.yaml` 里对应模型的覆盖值。"]
    return "\n".join(L)


def _deadline_block(soon: list) -> list[str]:
    L = [f"## 下线倒计时（{DEADLINE_WITHIN} 天内）", ""]
    for key, name, day, days, origin in soon:
        L.append(f"- **{name}** (`{key}`)：{day}，还有 {days} 天（据{origin}）")
    L.append("")
    return L
