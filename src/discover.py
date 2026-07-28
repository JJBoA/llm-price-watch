"""发现「源里有、但 models.yaml 还没登记」的模型。

models.yaml 是一份白名单，fetch.collect() 只遍历你手工登记过的 key——
所以厂商发了新模型，原本这个工具会一声不响。这个模块负责补上那个盲区。

策略是「快照 + 增量」，不是「全量对比」：
源里五家的对话模型有 200 多个，未纳管的一次能列出 30 条以上（绝大多数是
你已经知道的老型号），全报出来没人看。所以首次运行把当前未纳管集合整体
记进 data/discovered.json 且不算变化，之后每次只报「相对上次新出现的」。
稳态下每周 0～2 条，正好是真正的新模型。

三层降噪，缺一层报告就会淹掉：
  1. ignore 正则   —— 结构性噪音（ft: 微调、语音 / 音乐 / 向量模型、-latest 别名）
  2. 族归并        —— gpt-5.4-2026-03-05 归到 gpt-5.4，已纳管就不再报
  3. retired 匹配  —— retired.yaml 里写过的老型号不再提醒
"""
from __future__ import annotations

import re

# ---- 默认发现范围。models.yaml 里的 discovery: 块可整体覆盖 ----
DEFAULTS = {
    # LiteLLM 的 litellm_provider 字段值，决定"只看这五家第一方"
    "providers": ["openai", "gemini", "anthropic", "deepseek", "xai"],
    # 注意 responses：gpt-5.x-pro / codex 这批在源里 mode 是 responses 而不是
    # chat，漏了它就等于漏掉 OpenAI 最新的旗舰档
    "modes": ["chat", "responses"],
    "ignore": [
        r"^ft:",                      # 微调派生条目
        r"audio", r"realtime", r"-tts$", r"-live-", r"omni-",
        r"lyria", r"veo", r"imagen", r"-image",   # 音乐 / 视频 / 图像
        r"gemma", r"robotics", r"learnlm",        # 开源权重 / 专用实验模型
        r"embedding", r"moderation", r"rerank",
        r"container",
        r"search-preview", r"search-api", r"deep-research", r"computer-use",
        r"-customtools$",
        r"-latest$",                  # 指针别名，永远跟着正式名走
        r"-exp-?\d*$",                # 实验版
        r"-vision", r"-16k$",
        r"^gpt-4-\d{4}-preview$", r"^gpt-4-turbo-preview$",
    ],
}

_PREFIX = re.compile(r"^(?:openai|gemini|deepseek|xai|anthropic|vertex_ai)/")
_DATE = [re.compile(p) for p in (
    r"-\d{4}-\d{2}-\d{2}$",   # -2026-03-05
    r"-\d{8}$",               # -20250514
    r"-\d{2}-\d{4}$",         # -09-2025
    r"-\d{2}-\d{2}$",         # -06-17
    r"-\d{4}$",               # -1212 / -0309
)]
_SUFFIX = re.compile(r"-(?:latest|beta|preview)$")
_INFIX = re.compile(r"-beta-")


def family(key: str) -> str:
    """把带日期快照 / 前缀 / 别名后缀的 key 归一到「族名」。

    gpt-5.4-2026-03-05                  -> gpt-5.4
    xai/grok-2-1212                     -> grok-2
    deepseek/deepseek-v4-flash          -> deepseek-v4-flash
    gemini/gemini-3.1-flash-lite-preview-> gemini-3.1-flash-lite
    xai/grok-4.20-beta-0309-reasoning   -> grok-4.20-0309-reasoning

    剥掉 -preview / -beta 是有意的：同一个模型常常同时以 preview 名和正式名
    出现在源里（价格一模一样），只该在表格里占一行。真正的新模型即使只有
    preview 名，剥完也还是个没见过的族名，照样报得出来。
    """
    k = _INFIX.sub("-", _PREFIX.sub("", key))
    for _ in range(3):                      # 少数 key 有两段日期，多剥几轮
        for pat in _DATE:
            stripped = pat.sub("", k)
            if stripped != k:
                k = stripped
                break
        else:
            break
    while True:                             # -preview-latest 这类叠加后缀
        stripped = _SUFFIX.sub("", k)
        if stripped == k:
            return k
        k = stripped


def retired_families(retired_cfg: dict) -> set[str]:
    """从 retired.yaml 第二列的中文描述里抽出型号族名。

    那一列是人写的散文，形如
        "gpt-5-codex / gpt-5.1-codex / gpt-5.2-codex"
        "Gemini 2.0 Flash / 2.0 Flash-Lite"
        "Claude Opus 4（$15 / $75，旧表里有）"
    抽不干净不影响正确性——漏抽只是让 --list-unmanaged 多列一条已下线型号，
    不会漏报新模型（新模型靠 discovered.json 快照判断，见 run.py）。

    注意括号要在切分之前剥掉：先切 '/' 的话，'Claude Haiku 3.5（$0.80 / $4）'
    会被切成 '...3.5（$0.80' 和 '$4）' 两截，括号配不上对，抽出来全是垃圾。
    """
    out: set[str] = set()
    for item in retired_cfg.get("retired") or []:
        if len(item) < 2:
            continue
        text = re.sub(r"（.*?）|\(.*?\)", "", str(item[1]))
        for token in re.split(r"[/,、]", text):
            token = token.strip()
            if not token:
                continue
            # 形态一：本身就是 API 名（gpt-5-codex）
            m = re.match(r"^[A-Za-z0-9][\w.\-]*", token)
            if m:
                out.add(family(m.group(0).lower()))
            # 形态二：带空格的展示名（Gemini 2.0 Flash -> gemini-2.0-flash）
            kebab = re.sub(r"[^\w.\-]", "", re.sub(r"\s+", "-", token.lower()))
            if kebab:
                out.add(family(kebab))
    # 只保留长得像模型名的。三条都是排掉抽取残渣，别加「必须含数字」——
    # deepseek-chat / deepseek-reasoner 这些正经模型名里根本没数字。
    return {f for f in out
            if "-" in f                              # 排掉 'claude' / 'gemini' / '2.0'
            and not f.startswith("-")                # 排掉 '-non-reasoning' 这种续写片段
            and not re.search(r"[一-鿿]", f)}        # 排掉 '4旧表里有' 这种没剥净的中文


def _rules(cfg: dict) -> dict:
    d = dict(DEFAULTS)
    d.update(cfg.get("discovery") or {})
    return d


def candidates(raw: dict, cfg: dict, retired_cfg: dict) -> dict[str, dict]:
    """返回 {未纳管的 key: 精简价格信息}。"""
    rules = _rules(cfg)
    provs = set(rules["providers"])
    modes = set(rules["modes"])
    ignore = [re.compile(p) for p in rules["ignore"]]

    # alias 是「源里这几个 key 指的就是本行这个模型」，例如 gpt-5.6 是
    # gpt-5.6-sol 的别名。族归并推不出这种厂商特定的指向关系，只能显式声明。
    managed: set[str] = set()
    for prov in cfg["providers"]:
        for m in prov["models"]:
            managed.add(m["key"])
            managed.update(m.get("alias") or [])
    known_fams = {family(k) for k in managed} | retired_families(retired_cfg)

    out: dict[str, dict] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue                                    # 源顶层有个 sample_spec 说明条目
        if entry.get("litellm_provider") not in provs or entry.get("mode") not in modes:
            continue
        if key in managed or any(p.search(key) for p in ignore):
            continue
        if family(key) in known_fams:
            continue
        out[key] = {
            "input": _per_m(entry.get("input_cost_per_token")),
            "cached": _per_m(entry.get("cache_read_input_token_cost")),
            "output": _per_m(entry.get("output_cost_per_token")),
            "context": entry.get("max_input_tokens"),
            "provider": entry.get("litellm_provider"),
            "mode": entry.get("mode"),
        }
    return out


def _per_m(v):
    try:
        return round(float(v) * 1_000_000, 6)
    except (TypeError, ValueError):
        return None


def group(keys) -> dict[str, list[str]]:
    """按族名归并，同一族的多个快照只占报告一行。"""
    out: dict[str, list[str]] = {}
    for k in sorted(keys):
        out.setdefault(family(k), []).append(k)
    return out


def yaml_hint(key: str, rec: dict, primary: bool = True) -> str:
    """生成可直接粘进 models.yaml 的一行，省得手敲。

    primary=False 用于 --list-unmanaged：那个清单里绝大多数是老型号，
    默认给 primary: true 会误导人以为该按主力档收录。
    """
    price = []
    for field, label in (("input", "input"), ("cached", "cached"), ("output", "output")):
        v = rec.get(field)
        price.append(f"{label} ${v:g}" if v is not None else f"{label} —")
    flags = "primary: true, " if primary else ""
    return (f"      - {{key: {key}, {flags}status: 待定}}"
            f"    # 源报 {' / '.join(price)}")
