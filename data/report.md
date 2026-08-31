# 模型价格变更报告 · 2026-08-31

## 价格 / 参数变动

- **gpt-5.6-sol（别名 gpt-5.6）** (`gpt-5.6-sol`)
  - 输入 $5 → $4（-20%）
  - 缓存输入 $0.5 → $0.4（-20%）
  - 输出 $30 → $20（-33%）
  - 上下文 1,050,000 → 922,000（-12%）
- **gpt-5.6-terra** (`gpt-5.6-terra`)
  - 输入 $2.5 → $2（-20%）
  - 缓存输入 $0.25 → $0.2（-20%）
  - 输出 $15 → $12（-20%）
  - 上下文 1,050,000 → 922,000（-12%）
- **gpt-5.6-luna** (`gpt-5.6-luna`)
  - 输入 $1 → $0.2（-80%）
  - 缓存输入 $0.1 → $0.02（-80%）
  - 输出 $6 → $1.2（-80%）
  - 上下文 1,050,000 → 922,000（-12%）
- **gpt-5.4-mini** (`gpt-5.4-mini`)
  - 上下文 1,050,000 → 272,000（-74%）
- **gpt-5.4-nano** (`gpt-5.4-nano`)
  - 上下文 1,050,000 → 272,000（-74%）
- **Gemini 3.6 Flash** (`gemini/gemini-3.6-flash`)
  - 输入 $1.5 → $0.75（-50%）
  - 缓存输入 $0.15 → $0.075（-50%）
  - 输出 $7.5 → $3.75（-50%）
- **deepseek-v4-flash** (`deepseek-v4-flash`)
  - 输入 $0.14 → $0.44（+214%）
  - 缓存输入 $0.0028 → $0.014（+400%）
  - 输出 $0.28 → $1.32（+371%）
- **deepseek-v4-pro** (`deepseek-v4-pro`)
  - 输入 $0.435 → $1.32（+203%）
  - 缓存输入 $0.003625 → $0.044（+1114%）
  - 输出 $0.87 → $3.96（+355%）
- **grok-4.20-0309-reasoning** (`xai/grok-4.20-0309-reasoning`)
  - 输入 $2 → $1.25（-38%）
  - 输出 $6 → $2.5（-58%）
  - 上下文 2,000,000 → 1,000,000（-50%）
- **grok-4.20-0309-non-reasoning** (`xai/grok-4.20-beta-0309-non-reasoning`)
  - 输入 $2 → $1.25（-38%）
  - 输出 $6 → $2.5（-58%）
  - 上下文 2,000,000 → 1,000,000（-50%）
- **grok-4.20-multi-agent-0309** (`xai/grok-4.20-multi-agent-beta-0309`)
  - 输入 $2 → $1.25（-38%）
  - 输出 $6 → $2.5（-58%）
  - 上下文 2,000,000 → 1,000,000（-50%）

## 价格源出现未纳管的新模型

以下型号在源里有价，但 `config/models.yaml` 没登记，所以**不在表格里**。确认要收录就把对应行粘进 models.yaml：

- **claude-mythos**：输入 $10 / 缓存 $1 / 输出 $50 / 上下文 1,000,000

  ```yaml
        - {key: claude-mythos-preview, primary: true, status: 待定}    # 源报 input $10 / cached $1 / output $50
  ```
- **gemini-3.7-flash**：输入 $0.75 / 缓存 $0.075 / 输出 $3.75 / 上下文 1,048,576

  ```yaml
        - {key: gemini/gemini-3.7-flash, primary: true, status: 待定}    # 源报 input $0.75 / cached $0.075 / output $3.75
  ```
- **gpt-5.6-cyber**：输入 $12.5 / 缓存 $1.25 / 输出 $75 / 上下文 400,000

  ```yaml
        - {key: gpt-5.6-cyber, primary: true, status: 待定}    # 源报 input $12.5 / cached $1.25 / output $75
  ```
- **grok-4.20**：输入 $1.25 / 缓存 $0.2 / 输出 $2.5 / 上下文 1,000,000

  ```yaml
        - {key: xai/grok-4.20, primary: true, status: 待定}    # 源报 input $1.25 / cached $0.2 / output $2.5
  ```
- **grok-4.20-non-reasoning**：输入 $1.25 / 缓存 $0.2 / 输出 $2.5 / 上下文 1,000,000

  ```yaml
        - {key: xai/grok-4.20-non-reasoning, primary: true, status: 待定}    # 源报 input $1.25 / cached $0.2 / output $2.5
  ```
- **grok-4.20-reasoning**：输入 $1.25 / 缓存 $0.2 / 输出 $2.5 / 上下文 1,000,000

  ```yaml
        - {key: xai/grok-4.20-reasoning, primary: true, status: 待定}    # 源报 input $1.25 / cached $0.2 / output $2.5
  ```
- **grok-4.6**：输入 $2 / 缓存 $0.5 / 输出 $6 / 上下文 500,000

  ```yaml
        - {key: xai/grok-4.6, primary: true, status: 待定}    # 源报 input $2 / cached $0.5 / output $6
  ```

## 未纳管条目从价格源消失

这些本来就不在表格里，只是顺手告诉你源那边删了：

- `xai/grok-2`
- `xai/grok-2-1212`
- `xai/grok-beta`

## ⚠ 已过下线日期，仍留在表格里

价格源标了下线日期、但你的 `status` 里没写——两边对不上，得你判断谁对：

- **Claude Opus 4.1** (`claude-opus-4-1`)：源说 2026-08-05 下线（已过 26 天），你标的是「已弃用（deprecated）」

两种处理方式：源是对的 → 挪进 `retired.yaml`；源是错的（它对下线日期覆盖得不全，也会写错）→ 在那行加 `expired_ok: true` 永久静音。

## 下线倒计时（60 天内）

- **Claude Sonnet 4.5** (`claude-sonnet-4-5`)：2026-09-29，还有 29 天（据源）
- **Claude Haiku 4.5** (`claude-haiku-4-5`)：2026-10-15，还有 45 天（据源）
- **gpt-4.1-nano** (`gpt-4.1-nano`)：2026-10-23，还有 53 天（据配置）
- **o4-mini** (`o4-mini`)：2026-10-23，还有 53 天（据配置）
- **o3-mini** (`o3-mini`)：2026-10-23，还有 53 天（据配置）
- **o1** (`o1`)：2026-10-23，还有 53 天（据配置）
- **o1-pro** (`o1-pro`)：2026-10-23，还有 53 天（据配置）
- **gpt-4-turbo** (`gpt-4-turbo`)：2026-10-23，还有 53 天（据配置）
- **gpt-4** (`gpt-4`)：2026-10-23，还有 53 天（据配置）
- **gpt-3.5-turbo** (`gpt-3.5-turbo`)：2026-10-23，还有 53 天（据配置）

## 价格源新标注了下线日期

- `gpt-4.1-nano`：2026-10-23
- `o4-mini`：2026-10-23
- `o3-mini`：2026-10-23
- `o1`：2026-10-23
- `o1-pro`：2026-10-23
- `gpt-4-turbo`：2026-10-23
- `gpt-4`：2026-10-23
- `gpt-3.5-turbo`：2026-10-23
- `gemini/gemini-3.1-flash-lite`：2027-05-07
- `claude-fable-5`：2027-06-09
- `claude-opus-5`：2027-07-24
- `claude-opus-4-8`：2027-05-28
- `claude-opus-4-7`：2027-04-16
- `claude-opus-4-6`：2027-02-05
- `claude-opus-4-5`：2026-11-24
- `claude-sonnet-5`：2027-06-30
- `claude-sonnet-4-6`：2027-02-17
- `claude-sonnet-4-5`：2026-09-29
- `claude-haiku-4-5`：2026-10-15
- `claude-opus-4-1`：2026-08-05
- `claude-opus-4-20250514`：2026-06-15
- `claude-sonnet-4-20250514`：2026-06-15

## 主源改了口径（表格数字未变）

这些字段你在 models.yaml 里锁定过，所以表格不受影响。但主源那边的值动了——如果它已经跟官网一致，覆盖就可以撤掉了：

- **grok-4.5** (`xai/grok-4.5`)
  - 源报缓存输入 $0.5 → $0.3

## 校验源（OpenRouter）改价了

主源还没动。可能是官网真改价了、OpenRouter 先反映出来，也可能只是它自己在打折——值得核对一眼官网：

- **gpt-5.6-sol（别名 gpt-5.6）** (`gpt-5.6-sol`)
  - 输入 $5 → $2
  - 缓存输入 $0.5 → $0.2
  - 输出 $30 → $10
- **gpt-5.6-terra** (`gpt-5.6-terra`)
  - 输入 $1.25 → $2
  - 缓存输入 $0.125 → $0.2
  - 输出 $7.5 → $12
- **gpt-5.6-luna** (`gpt-5.6-luna`)
  - 输入 $0.5 → $0.2
  - 缓存输入 $0.05 → $0.02
  - 输出 $3 → $1.2
- **Gemini 3.6 Flash** (`gemini/gemini-3.6-flash`)
  - 输入 $1.5 → $0.75
  - 缓存输入 $0.15 → $0.075
  - 输出 $7.5 → $3.75
- **deepseek-v4-flash** (`deepseek-v4-flash`)
  - 输入 $0.14 → $0.088606
  - 缓存输入 $0.028 → $0.017721
  - 输出 $0.28 → $0.177212
- **deepseek-v4-pro** (`deepseek-v4-pro`)
  - 输入 $0.435 → $1.6
  - 缓存输入 $0.003625 → $0.135
  - 输出 $0.87 → $3.2

## 官方页面内容有变动

价格源不一定同步了，建议点开看一眼有没有新的下线公告或分档规则：

- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/deprecations
- https://ai.google.dev/gemini-api/docs/pricing
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/about-claude/model-deprecations
- https://api-docs.deepseek.com/quick_start/pricing
- https://docs.x.ai/developers/pricing

## 仅供参考（持续状态，无需处理）

- ℹ `gpt-5.6-sol` 的 input 两源不一致：主源 4.0 vs OpenRouter 2.0，建议核对官网
- ℹ `gpt-5.6-sol` 的 output 两源不一致：主源 20.0 vs OpenRouter 10.0，建议核对官网
- ℹ `vertex_ai/claude-3-5-haiku` 的 input：配置里锁定为 0.8，价格源报 1.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `vertex_ai/claude-3-5-haiku` 的 output：配置里锁定为 4.0，价格源报 5.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `deepseek-v4-flash` 的 input 两源不一致：主源 0.44 vs OpenRouter 0.088606，建议核对官网
- ℹ `deepseek-v4-flash` 的 output 两源不一致：主源 1.32 vs OpenRouter 0.177212，建议核对官网
- ℹ `deepseek-v4-pro` 的 input 两源不一致：主源 1.32 vs OpenRouter 1.6，建议核对官网
- ℹ `deepseek-v4-pro` 的 output 两源不一致：主源 3.96 vs OpenRouter 3.2，建议核对官网

---
确认无误后，把新的 `data/baseline.json` 和 xlsx 合入即可；
如果发现价格源报错，请改 `config/models.yaml` 里对应模型的覆盖值。