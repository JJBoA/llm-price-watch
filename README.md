# 模型 API 价格监控

定期检查 OpenAI / Google / Anthropic / DeepSeek / xAI 的文本模型价格，
有变动时给出变更报告并重新生成表格。

**设计前提：这个工具的职责是「发现变化」，不是「保证正确」。**
自动源出错是常态（首次搭建时就抓到三处），所以默认行为是报差异 + 开 PR 等人确认，
从不静默覆盖已确认的数据。

---

## 快速开始

### 本地手动跑

```bash
pip install -r requirements.txt

python run.py            # 只看差异，不动任何文件
python run.py --write    # 确认没问题后落盘：更新 baseline + 重新生成 xlsx
python run.py --force --write   # 没变化也强制重新生成 xlsx
python run.py --skip-pages      # 跳过官网页面检查（快很多）
python run.py --list-unmanaged  # 列出源里所有「还没登记」的型号，供一次性复核
```

退出码：`0` 无需处理 · `1` 有需要确认的变化 · `2` 抓取失败。

### 云端定时

首次搭建（只需做一次）：

```bash
git init && git add -A && git commit -m "init"
git branch -M main
# 在 GitHub 上建一个空仓库（不要勾选 README / .gitignore），然后：
git remote add origin git@github.com:<你的账号>/llm-price-watch.git
git push -u origin main
```

推上去之后自动生效，无需额外配置：

- **每天北京时间 9:00** 自动跑一次（改 `.github/workflows/update.yml` 里的 cron 可调）
- Actions 页面有 **Run workflow** 按钮可随时手动触发
- 有变动时自动开一个 PR，正文就是变更报告；合并即采纳，不合并就当没发生
- 无论有无变动，xlsx 都作为 artifact 挂 90 天，可直接下载

> 需要在仓库 Settings → Actions → General → Workflow permissions
> 勾选 **Read and write permissions**，否则 bot 建不了 PR。

---

## 数据源

| 层级 | 来源 | 作用 |
|---|---|---|
| 主源 | [LiteLLM `model_prices_and_context_window.json`](https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json) | 一次请求拿全五家，结构化字段 |
| 校验 | OpenRouter `/api/v1/models` | 两源差异 >2% 时告警（不通则自动跳过） |
| 兜底 | 各家官方页面 | 只存正文哈希，页面一变就提醒你人工去看 |

为什么不直接爬官网：OpenAI 的老型号折叠在 JS 控制的 "All models" 区块里，
Google 的价格页整页由 JS 渲染，直接抓都拿不到内容，选择器一改还会静默出错。

---

## 它到底能发现什么

| 情况 | 怎么发现的 |
|---|---|
| 已登记模型改价 / 改上下文 | 和 `data/baseline.json` 逐字段对比 |
| **厂商发了新模型**（你还没登记） | 扫全源，减掉白名单和 `retired.yaml`，报「相对上次快照新出现的」 |
| 已登记模型从源里消失 | 取价时查不到 → 「需要人工判断」 |
| 官方新标了下线日期 | 源的 `deprecation_date` 变了 |
| **下线日期快到了 / 已过期** | 拿源的日期和 `status` 里手写的日期比今天 |
| 主源改了你锁定过的字段 | 影子字段 `*_auto` 对比。表格数字不变，但提示你覆盖可能能撤了 |
| **校验源先改价了**（主源还没动） | 影子字段 `*_or` 对比，当早期信号用 |
| 官方页面正文变了 | SHA256 哈希对比，只提醒「去看看」，不解析内容 |

### 新模型发现是怎么做到不吵的

源里五家的对话模型有 200 多个，未纳管的一次能列出 30 多条（绝大多数是你早就
知道的老型号）。全报出来没人看，所以用的是**快照 + 增量**：首次运行把当前
未纳管集合整体记进 `data/discovered.json` 且不逐条列出，之后只报相对这份快照
**新出现的**。稳态下每周 0～2 条，正好是真正的新模型，报告里还会附一行可以
直接粘进 `models.yaml` 的 yaml。

想一次性复核那几十条历史遗留，跑 `python run.py --list-unmanaged`。
报告里冒出不想看的东西（新的语音模型、实验版），往 `models.yaml` 的
`discovery.ignore` 里加一条正则就行。

### 「有变化」的定义（决定 CI 要不要开 PR）

提示分两档，这个区分很重要：

- **需要处理** → 退出码 `1`，CI 开 PR。改价、新模型、源里消失、页面变动、已过下线日期。
- **仅供参考** → 不触发。配置锁定值与源不一致、两源有分歧——这些是**持续存在**的
  已知状态（你手工纠正过源的错误，这个状态不会自己消失）。算进「有变化」的话，
  CI 会每周开一个内容完全相同的 PR，两个月后你就不看了。

所以看到「仅供参考」栏目里常驻那几条，不用管，那是正常的。

---

## 日常维护

只需要改 `config/` 下两个文件：

**`config/models.yaml`** —— 受管模型清单。新增模型就加一行，
`key` 填价格源里的键名（不确定就先随便填，跑一次看报错提示）。

覆盖自动值的写法：

```yaml
- {key: xai/grok-4.5, cached: 0.30}    # 锁定数值，与源不一致时报告里会留痕
- {key: gemini/gemini-3-pro-preview, cached: 待核}   # 官网没公布，留空并标注
- {key: gpt-5.5-pro, cached: 无}                     # 官方明确不提供该档，显示 —
- {key: xai/grok-build-0.1, manual_only: true, input: 1.0, output: 2.0}  # 源里没有，全手工
- {key: claude-opus-4-20250514, expired_ok: true}    # 明知过期仍要留在表里，别再告警
- {key: gpt-5.6-sol, alias: [gpt-5.6]}   # 声明别名，否则 gpt-5.6 会被当成「新模型」重复报
```

`alias` 的用处：源里常常同一个模型有多个 key。同族的（`gpt-5.4-2026-03-05`
之于 `gpt-5.4`、`gemini-3.1-flash-lite-preview` 之于 `gemini-3.1-flash-lite`）
族归并会自动认出来；但 `gpt-5.6` → `gpt-5.6-sol` 这种厂商特定的指向关系推不出来，
得显式声明。判断依据很简单：**两个 key 在源里逐字段同价，就是别名，不该在表里占两行。**

同一个文件末尾还有个 `discovery:` 块，管的是新模型发现的范围和降噪规则，
一般不用动；报告里出现不想看的型号时往 `ignore` 加正则。

**`config/retired.yaml`** —— 已彻底下线的型号。
报告提示「从价格源消失」时，确认后把条目挪进来。
挪进来还有个副作用是好的：发现逻辑会认得这些名字，不再把它们当「未纳管的新模型」报出来。

---

## 这套东西覆盖不到什么

说清楚比假装全自动有用：

- **新模型的延迟**。发现新模型靠的是 LiteLLM 那份 JSON，它更新有滞后，
  厂商发布当天不一定能看到。要更及时只能盯页面哈希那条线人工去看。
- **新模型不会自动进表格**。报告只告诉你「源里多了个 X，价格是多少」，
  收不收录、叫什么名字、算不算主力档，得你决定——这些信息源里没有。
  报告会附一行现成的 yaml，粘过去就行。
- **下线日期**。价格源的 `deprecation_date` 覆盖不全（也会写错，`gemini-3-pro-preview`
  就被标了个不对的日期），像 OpenAI 7/23 那批 codex 停服、
  DeepSeek 别名硬下线，都只写在 prose 页面里。所以才有页面哈希监控——
  它只告诉你「这页变了，去看看」，不解析内容。
- **分档规则**。长上下文加价、缓存写入倍率、Batch 折扣、促销到期回调，
  源里通常只存一个主价，这些得写在 `note` 里手工维护。
- **官网压根没公布的数字**。标 `待核` 的那些，任何自动化都变不出来。

---

## 目录

```
run.py                    入口，云端和本地共用
config/models.yaml        受管模型清单 + 发现规则（主要维护这个）
config/retired.yaml       已下线型号
src/fetch.py              抓取 + 归一化 + 交叉校验
src/discover.py           白名单之外的新模型发现 + 降噪
src/diff.py               对比 baseline，生成人话报告
src/build_xlsx.py         渲染表格
data/baseline.json        上次结果，diff 的基准
data/pages.json           官网页面哈希
data/discovered.json      未纳管型号快照，新模型发现的基准
data/report.md            最近一次变更报告
API文本价格.xlsx           产出
```

`data/` 下这三个 json 都是状态文件，**必须提交进 git**，否则云端每次运行
都从零开始，永远发现不了增量。
