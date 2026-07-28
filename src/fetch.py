"""拉取并归一化各家模型价格。

主源：LiteLLM 的 model_prices_and_context_window.json（结构化，覆盖全部五家）
校验源：OpenRouter /api/v1/models（可选，网络不通时自动跳过）

提示分两档，这个区分决定 CI 要不要开 PR：
  alerts  —— 需要你动手的（受管 key 在源里查不到）
  notices —— 持续存在的已知状态（配置锁定值与源不一致、两源有分歧）
后者每次运行都会出现，若也算「有变化」，CI 就会每周开一个内容相同的 PR，
两个月后你就不看了。所以 notices 只进报告，不触发通知。
真正的「源改了主意」由 diff 模块通过 *_auto / *_or 影子字段捕获。
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from typing import Any

import requests

LITELLM_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
M = 1_000_000
TIMEOUT = 60


def _per_m(v: Any) -> float | None:
    """每 token 单价 → 每 1M tokens 单价。"""
    if v is None:
        return None
    try:
        return round(float(v) * M, 6)
    except (TypeError, ValueError):
        return None


def fetch_litellm() -> dict[str, dict]:
    r = requests.get(LITELLM_URL, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_openrouter() -> dict[str, dict]:
    """校验源。拿不到就返回空字典，不让整个流程失败。"""
    try:
        r = requests.get(OPENROUTER_URL, timeout=TIMEOUT)
        r.raise_for_status()
        out = {}
        for m in r.json().get("data", []):
            p = m.get("pricing") or {}
            out[m["id"]] = {
                "input": _per_m(p.get("prompt")),
                "output": _per_m(p.get("completion")),
                "cached": _per_m(p.get("input_cache_read")),
            }
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] OpenRouter 校验源不可用，跳过交叉校验：{exc}")
        return {}


def normalize(raw: dict, key: str) -> dict | None:
    """从价格源里取出一个模型，转成统一结构。"""
    e = raw.get(key)
    if e is None:
        return None
    return {
        "input": _per_m(e.get("input_cost_per_token")),
        "cached": _per_m(e.get("cache_read_input_token_cost")),
        "output": _per_m(e.get("output_cost_per_token")),
        "cache_write": _per_m(e.get("cache_creation_input_token_cost")),
        "context": e.get("max_input_tokens"),
        "deprecation_date": e.get("deprecation_date"),
    }


def collect(cfg: dict, raw: dict | None = None) -> tuple[dict[str, dict],
                                                         list[str], list[str]]:
    """按配置抓取全部受管模型。

    raw 可传入已抓好的价格源，避免和模型发现重复请求一次。
    返回 (数据, alerts, notices)。
    """
    if raw is None:
        raw = fetch_litellm()
    xref = fetch_openrouter()
    data: dict[str, dict] = {}
    alerts: list[str] = []
    notices: list[str] = []

    for prov in cfg["providers"]:
        for m in prov["models"]:
            key = m["key"]
            rec = normalize(raw, key)
            if rec is None:
                if not m.get("manual_only"):
                    alerts.append(
                        f"⚠ `{key}` 在价格源中查不到——可能已被移除或改名，需人工确认")
                rec = {"input": None, "cached": None, "output": None,
                       "cache_write": None, "context": None, "deprecation_date": None}
            rec["company"] = prov["company"]
            rec["name"] = m.get("name", key)
            rec["status"] = m.get("status", "")
            rec["expired_ok"] = bool(m.get("expired_ok"))

            # 人工覆盖：与源不一致时留痕，不静默吞掉。
            # 源报的原值存进 *_auto，下次源自己改了 diff 就能发现（那才是真新闻）。
            for field in ("input", "cached", "output", "context"):
                if field in m:
                    manual = m[field]
                    auto = rec.get(field)
                    rec[f"{field}_auto"] = auto
                    rec[field] = manual
                    if manual in ("待核", "无"):
                        rec[field] = None
                        if manual == "待核":
                            rec["flag_" + field] = "待核"
                    elif auto is not None and float(manual) != float(auto):
                        notices.append(
                            f"ℹ `{key}` 的 {field}：配置里锁定为 {manual}，"
                            f"价格源报 {auto}（已按配置输出，如源已修正请更新 models.yaml）"
                        )

            # 与 OpenRouter 交叉校验。两源的值也存进 *_or 当第二个变更探测器：
            # 主源漏更新时，OpenRouter 那边一动 diff 就会报出来。
            # 按短名匹配，但要求唯一命中。原来是「第一个匹配胜出」，选中谁取决于
            # API 返回顺序——一旦出现同名条目，*_or 就会在两个值之间来回跳，
            # 每周生成一条假的「OpenRouter 改价」。宁可放弃校验也不要不确定的值。
            short = key.split("/")[-1]
            hits = [v for k2, v in xref.items() if k2.split("/")[-1] == short]
            if len(hits) == 1:
                or_val = hits[0]
                for field in ("input", "output", "cached"):
                    b = or_val.get(field)
                    if b is not None:
                        rec[f"{field}_or"] = b
                    a = rec.get(field)
                    if field != "cached" and a and b and \
                            abs(a - b) / max(a, b) > 0.02:
                        notices.append(
                            f"ℹ `{key}` 的 {field} 两源不一致："
                            f"主源 {a} vs OpenRouter {b}，建议核对官网"
                        )
            elif len(hits) > 1:
                notices.append(
                    f"ℹ `{key}` 在 OpenRouter 有 {len(hits)} 个同名条目，"
                    f"无法确定对应哪个，已跳过交叉校验")

            data[key] = rec

    return data, alerts, notices


# 页面哈希算法版本号。存进 pages.json 当前缀，换算法时靠它识别出旧基准
# 需要重建，而不是把 7 个页面全报成「内容变了」。
PAGE_ALGO = "t1:"

_DROP = re.compile(r"<(script|style|noscript|svg|template)\b[^>]*>.*?</\1\s*>",
                   re.S | re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_BLOCK = re.compile(r"<(main|article)\b[^>]*>(.*?)</\1\s*>", re.S | re.I)


def _visible_text(markup: str) -> str:
    s = _DROP.sub(" ", markup)
    s = _COMMENT.sub(" ", s)
    s = _TAG.sub(" ", s)
    return _WS.sub(" ", html.unescape(s)).strip()


def page_text(markup: str) -> str:
    """抽出页面正文。取 <main> / <article> 里最长的那块，都没有就退回整页。

    为什么不直接哈希整个响应体（原来的做法）：Google 的页面每次请求都带一个新的
    <script nonce="...">，Anthropic 和 xAI 的标记里也有随请求变化的内容——实测
    7 个受监控页面里有 4 个每次抓都算「变了」，那样 CI 会每周开一个假 PR。
    只看可见正文既稳定，语义也更对：改个 CSS 不该惊动你，改了价格文案才该。

    为什么取最长的那块而不是固定用 <main>：Anthropic 文档的 <main> 只有 970 字，
    是个不含价格表的空壳，正文在 <article> 里；xAI 则相反，只有 <main>。
    """
    blocks = [_visible_text(m.group(2)) for m in _BLOCK.finditer(markup)]
    best = max(blocks, key=len, default="")
    return best if len(best) >= 200 else _visible_text(markup)


def page_fingerprints(cfg: dict) -> dict[str, str]:
    """对官方页面正文取哈希，用于发现「下线公告变了」这类无法结构化的改动。"""
    out = {}
    for prov in cfg["providers"]:
        for url in prov.get("watch", []):
            try:
                r = requests.get(url, timeout=TIMEOUT,
                                 headers={"User-Agent": "llm-price-watch/1.0"})
                r.raise_for_status()
                digest = hashlib.sha256(
                    page_text(r.text).encode("utf-8")).hexdigest()[:16]
                out[url] = PAGE_ALGO + digest
            except Exception as exc:  # noqa: BLE001
                out[url] = f"ERROR: {type(exc).__name__}"
    return out


if __name__ == "__main__":
    import yaml
    with open("config/models.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    d, a, n = collect(cfg)
    print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
    print("\n".join(a + n))
