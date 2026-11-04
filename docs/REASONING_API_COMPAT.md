# OpenAI-compatible reasoning controls for the selected local models

The current DeepSeek1017 profile uses its native thinking format, with author default high75. Its config's reason_mode=off disables separate author-mode routing, not thinking. Auto/Adaptive/Ultra belong only to the specifically qualified DavidAU model and are not enabled for DeepSeek.

The canonical requested OpenAI effort words work in both interfaces:

| API word | DeepSeek native hint |
| --- | ---: |
| low | 50 |
| medium | 62 |
| high | 75 |
| xhigh | 100, official max alias |

The official DeepSeek encoder defines low/high/max as50/75/100 and accepts integer hints1..100. Medium62 is the selected template's compatibility level, not a separately named official trained mode. These values are hints, not token budgets or promises of identical reasoning strength to OpenAI models. The canonical spelling is xhigh. Explicit per-request effort takes precedence over the saved default. Other model families retain their own native mappings/defaults.

Chat Completions:

```json
{"model":"local-model-id","messages":[{"role":"user","content":"Your task"}],"reasoning_effort":"high"}
```

Responses:

```json
{"model":"local-model-id","input":"Your task","reasoning":{"effort":"xhigh"}}
```

The author-recommended DeepSeek temperature1.0/top_p1.0 remain the saved defaults. Explicit client sampling values are honored. No extra penalty was introduced for reasoning. The configured context262144 is the user's hardware profile; the author's larger advertised window is not silently substituted. A small max_completion_tokens/max_output_tokens can exhaust reasoning plus final output; effort is not that token cap. When no cap is provided, the local server fits output to the remaining context. Raw local reasoning and the final answer are separate; no OpenAI Pro execution or universal model capability is implied.

Eight CPU cases exercised the deployed Chat/Responses normalizers, effective template and actual token IDs for the four requested levels. Additional default-high75, request precedence and synthetic reasoning/final splitting checks passed. These were CPU protocol/rendering checks, not eight new model generations or a broad reasoning-quality evaluation. The existing working behavior required no native rebuild, live helper change, credential change or model restart.

Sources: [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning), [DeepSeek1017 author sampling](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/README.md), [author prompt encoding](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/encoding/README.md).
