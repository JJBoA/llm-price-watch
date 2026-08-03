# 模型价格变更报告 · 2026-08-03

## 价格 / 参数变动

- **gpt-5.6-terra** (`gpt-5.6-terra`)
  - 输入 $2.5 → $2（-20%）
  - 缓存输入 $0.25 → $0.2（-20%）
  - 输出 $15 → $12（-20%）
- **gpt-5.6-luna** (`gpt-5.6-luna`)
  - 输入 $1 → $0.2（-80%）
  - 缓存输入 $0.1 → $0.02（-80%）
  - 输出 $6 → $1.2（-80%）
- **gpt-5.4-mini** (`gpt-5.4-mini`)
  - 上下文 1,050,000 → 272,000（-74%）
- **gpt-5.4-nano** (`gpt-5.4-nano`)
  - 上下文 1,050,000 → 272,000（-74%）

## 校验源（OpenRouter）改价了

主源还没动。可能是官网真改价了、OpenRouter 先反映出来，也可能只是它自己在打折——值得核对一眼官网：

- **gpt-5.6-terra** (`gpt-5.6-terra`)
  - 输入 $1.25 → $1
  - 缓存输入 $0.125 → $0.1
  - 输出 $7.5 → $6
- **gpt-5.6-luna** (`gpt-5.6-luna`)
  - 输入 $0.5 → $0.1
  - 缓存输入 $0.05 → $0.01
  - 输出 $3 → $0.6

## 官方页面内容有变动

价格源不一定同步了，建议点开看一眼有没有新的下线公告或分档规则：

- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/deprecations
- https://ai.google.dev/gemini-api/docs/pricing
- https://api-docs.deepseek.com/quick_start/pricing
- https://docs.x.ai/developers/pricing

## 仅供参考（持续状态，无需处理）

- ℹ `gpt-5.6-terra` 的 input 两源不一致：主源 2.0 vs OpenRouter 1.0，建议核对官网
- ℹ `gpt-5.6-terra` 的 output 两源不一致：主源 12.0 vs OpenRouter 6.0，建议核对官网
- ℹ `gpt-5.6-luna` 的 input 两源不一致：主源 0.2 vs OpenRouter 0.1，建议核对官网
- ℹ `gpt-5.6-luna` 的 output 两源不一致：主源 1.2 vs OpenRouter 0.6，建议核对官网
- ℹ `vertex_ai/claude-3-5-haiku` 的 input：配置里锁定为 0.8，价格源报 1.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `vertex_ai/claude-3-5-haiku` 的 output：配置里锁定为 4.0，价格源报 5.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `xai/grok-4.5` 的 cached：配置里锁定为 0.3，价格源报 0.5（已按配置输出，如源已修正请更新 models.yaml）

---
确认无误后，把新的 `data/baseline.json` 和 xlsx 合入即可；
如果发现价格源报错，请改 `config/models.yaml` 里对应模型的覆盖值。