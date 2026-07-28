#!/usr/bin/env python3
"""模型价格监控 —— 云端定时和本地手动共用这一个入口。

用法：
    python run.py              # 只检查，把变更报告打印到屏幕，什么都不改
    python run.py --write      # 确认无误后写入 baseline + 重新生成 xlsx
    python run.py --write --force   # 即使没变化也重新生成 xlsx
    python run.py --list-unmanaged  # 列出源里所有未纳管的型号，供一次性复核

退出码：0 = 无需处理；1 = 有需要你确认的变化（CI 靠这个决定要不要发通知）；2 = 抓取失败
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import date

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from src import build_xlsx, diff, discover, fetch  # noqa: E402

ROOT = pathlib.Path(__file__).parent
BASELINE = ROOT / "data" / "baseline.json"
PAGES = ROOT / "data" / "pages.json"
DISCOVERED = ROOT / "data" / "discovered.json"
REPORT = ROOT / "data" / "report.md"
XLSX = ROOT / "API文本价格.xlsx"


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_cfg() -> tuple[dict, dict]:
    cfg = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    retired = yaml.safe_load((ROOT / "config" / "retired.yaml").read_text(encoding="utf-8"))
    return cfg, retired


def list_unmanaged() -> int:
    """一次性复核用：把当前所有未纳管型号按族列出来。"""
    cfg, retired_cfg = load_cfg()
    raw = fetch.fetch_litellm()
    cand = discover.candidates(raw, cfg, retired_cfg)
    groups = discover.group(cand)

    print(f"价格源里有、但表格里没有的型号：{len(cand)} 条，归并成 {len(groups)} 族。\n")
    print("这不是待办清单。绝大多数是早就下线的老型号（Claude 3、Gemini 2.0、")
    print("Grok 2/3 那些），只是 retired.yaml 用中文散文写的、脚本没认出来而已。")
    print("日常你不用管这个命令 —— 真正新出现的型号会在 run.py 的报告里单独报。")
    print("这里的用途只有一个：首次搭建时扫一眼，确认没漏掉你正在用的型号。\n")

    for fam, keys in sorted(groups.items()):
        rec = cand[keys[0]]
        note = f"  （同族 {len(keys)} 条）" if len(keys) > 1 else ""
        print(f"  {fam:40s} 输入 ${rec['input'] or 0:<8g} 输出 ${rec['output'] or 0:<8g}{note}")

    print("\n" + "-" * 70)
    print("如果上面有你确实在用、该进表格的型号，照下面这行的格式加进")
    print("config/models.yaml（status / primary / note 得你自己判断填写）：\n")
    for fam, keys in sorted(groups.items()):
        print(discover.yaml_hint(keys[0], cand[keys[0]], primary=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="写入 baseline 并重新生成 xlsx")
    ap.add_argument("--force", action="store_true", help="无变化时也重新生成 xlsx")
    ap.add_argument("--skip-pages", action="store_true", help="跳过官网页面哈希检查")
    ap.add_argument("--list-unmanaged", action="store_true",
                    help="列出源里所有未纳管型号后退出，不做对比")
    args = ap.parse_args()

    if args.list_unmanaged:
        return list_unmanaged()

    today = date.today().isoformat()
    cfg, retired_cfg = load_cfg()

    print("[1/5] 拉取价格源 …")
    try:
        raw = fetch.fetch_litellm()
        new_data, alerts, notices = fetch.collect(cfg, raw)
    except Exception as exc:  # noqa: BLE001
        print(f"抓取失败：{exc}", file=sys.stderr)
        return 2
    print(f"      受管模型 {len(new_data)} 个")

    # ---- 白名单之外：源里有、models.yaml 没登记的型号 ----
    print("[2/5] 扫描未纳管的新模型 …")
    cand = discover.candidates(raw, cfg, retired_cfg)
    seen_state = load_json(DISCOVERED)
    seen = set(seen_state.get("candidates") or [])
    # 上次运行时仍在受管清单里的 key。没有这一层的话，你把一个模型从
    # models.yaml 挪进 retired.yaml 之后，它就不再受管、立刻变成「未纳管候选」，
    # 会被当成新模型报一次。retired.yaml 是人写的散文，靠匹配它不可靠。
    was_managed = set(seen_state.get("managed") or [])
    first_snapshot = None
    if not seen_state:
        # 首次运行不逐条报：一次能列出几十条老型号，全塞进报告没人看
        first_snapshot = len(cand)
        fresh, vanished = {}, {}
        print(f"      首次建立快照，记录 {len(cand)} 条（--list-unmanaged 可复核）")
    else:
        # 按族排除，不能只比精确 key：claude-haiku-4-5 一离开受管清单，
        # 它的日期快照 claude-haiku-4-5-20251001 也跟着落单，同样会被误报。
        # 这层只桥接「刚挪走」这一次，落盘后它们就进 candidates 快照了。
        was_fams = {discover.family(k) for k in was_managed}
        fresh = {k: v for k, v in cand.items()
                 if k not in seen and k not in was_managed
                 and discover.family(k) not in was_fams}
        # 「消失」要拿原始价格源判断，不能用 cand。快照里的 key 掉出 cand 有两种
        # 原因：源真删了，或者你新加了 ignore / alias 把它压掉了。后者不是消失，
        # 报出来只会让人以为厂商下线了什么。
        vanished = {k: None for k in seen if k not in raw}
        print(f"      未纳管 {len(cand)} 条，其中新出现 {len(fresh)} 条，消失 {len(vanished)} 条")
    groups = discover.group(fresh)
    hints = {keys[0]: discover.yaml_hint(keys[0], cand[keys[0]])
             for keys in groups.values()}

    print("[3/5] 对比上次结果 …")
    old_data = load_json(BASELINE)
    d = diff.compare(old_data, new_data) if old_data else {
        "added": [], "removed": [], "changed": [],
        "deprecations": [], "source_moves": [], "xref_moves": []}
    if not old_data:
        print("      首次运行，无对比基准")

    passed, soon = diff.deadlines(new_data, today)
    if passed:
        print(f"      ⚠ {len(passed)} 个模型已过下线日期")

    page_changes: list[str] = []
    old_pages = load_json(PAGES)
    new_pages = old_pages
    if args.skip_pages:
        print("[4/5] 跳过官网页面检查")
    else:
        print("[4/5] 检查官网页面是否变动 …")
        new_pages = fetch.page_fingerprints(cfg)
        rebased = 0
        for url, h in new_pages.items():
            if h.startswith("ERROR"):
                alerts.append(f"⚠ 页面抓取失败：{url}（{h}）")
            elif url in old_pages:
                old = old_pages[url]
                if not old.startswith(fetch.PAGE_ALGO):
                    # 旧基准是别的算法算的（或上次抓取失败），没法比，重建
                    rebased += 1
                elif old != h:
                    page_changes.append(url)
        if rebased:
            print(f"      {rebased} 个页面的基准用的是旧算法，本次重建，不报变动")

    changed = diff.has_changes(d, page_changes, alerts, fresh, vanished, passed)
    # 首次建立快照本身没有「变化」，但 discovered.json 必须落盘，否则 CI 里
    # 每次都是首次运行、快照永远存不住。算作一次变化，让 CI 把它提交掉。
    if first_snapshot is not None:
        changed = True
    report = diff.render(d, new_data, page_changes, alerts, notices, today,
                         discovered=fresh, gone=vanished, passed=passed, soon=soon,
                         groups=groups, hints=hints, first_snapshot=first_snapshot)

    print("[5/5] 生成报告 …\n")
    print(report)

    if args.write:
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(report, encoding="utf-8")
        BASELINE.write_text(json.dumps(new_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        PAGES.write_text(json.dumps(new_pages, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        DISCOVERED.write_text(json.dumps(
            {"date": today, "candidates": sorted(cand),
             "managed": sorted(new_data)},
            ensure_ascii=False, indent=2), encoding="utf-8")
        if changed or args.force or not XLSX.exists():
            build_xlsx.build(cfg, retired_cfg, new_data, today, str(XLSX))
            print(f"\n已写入 {XLSX.name} 和 data/ 下的状态文件")
        else:
            print("\n无变化，xlsx 未重新生成（要强制生成加 --force）")
    elif changed:
        print("\n（这是预览。确认无误后跑 `python run.py --write` 落盘）")

    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
