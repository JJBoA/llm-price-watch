# 模型价格变更报告 · 2026-07-28

本次检查未发现需要处理的变化。

## 仅供参考（持续状态，无需处理）

- ℹ `gpt-5.6-terra` 的 input 两源不一致：主源 2.5 vs OpenRouter 1.25，建议核对官网
- ℹ `gpt-5.6-terra` 的 output 两源不一致：主源 15.0 vs OpenRouter 7.5，建议核对官网
- ℹ `gpt-5.6-luna` 的 input 两源不一致：主源 1.0 vs OpenRouter 0.5，建议核对官网
- ℹ `gpt-5.6-luna` 的 output 两源不一致：主源 6.0 vs OpenRouter 3.0，建议核对官网
- ℹ `vertex_ai/claude-3-5-haiku` 的 input：配置里锁定为 0.8，价格源报 1.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `vertex_ai/claude-3-5-haiku` 的 output：配置里锁定为 4.0，价格源报 5.0（已按配置输出，如源已修正请更新 models.yaml）
- ℹ `xai/grok-4.5` 的 cached：配置里锁定为 0.3，价格源报 0.5（已按配置输出，如源已修正请更新 models.yaml）
