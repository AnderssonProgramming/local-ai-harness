# Infrastructure Stress Test: Optimizing a Local AI Harness

Methodology: an 8-file Python project (`stress_project/`) was built with one traceable
fact — `MAX_TASKS_PER_USER = 47` — planted only in `01_models.py`. The project was sent
to a local Ollama instance via its HTTP API (`/api/generate`) at increasing sizes, then
padded with unrelated filler code to force context overflow. All numbers below come from
Ollama's own response metadata (`prompt_eval_count`, `eval_count`, durations), not
estimates. Scripts: `run_stress_test.ps1` (checkpoint sweep) and `run_padded_test.ps1`
(forced-overflow test).

## Local Environment Hardware & Model Specs

- CPU: Intel Core i7-1255U (12th Gen, 10 cores / 12 threads)
- RAM: 32 GB
- GPU: Intel UHD Graphics (integrated — not supported by Ollama's acceleration
  backends, so inference is 100% CPU-bound)
- OS: Windows 11 Home
- Runtime: Ollama 0.32.5
- Model: `phi3:latest` (Phi-3-mini, 3.8B params, Q4_0 quantization, 2.2 GB on disk).
  Architecture metadata advertises a 131,072-token context length; the Modelfile sets
  no `num_ctx` override.

## Observed Performance Bottlenecks (Latency / Resource usage)

| Files | Real prompt tokens | Time-to-first-token | Total time | Gen. speed |
|---|---|---|---|---|
| 1 | 446 | 0.26s | 2.55s | 7.47 tok/s |
| 2 | 848 | 13.95s | 14.95s | 7.10 tok/s |
| 4 | 1,270 | 19.81s | 20.85s | 6.94 tok/s |
| 6 | 1,898 | 30.42s | 32.79s | 5.14 tok/s |
| 8 | 2,374 | 26.24s | 27.53s | 5.61 tok/s |

No GPU offload is possible on this hardware, so latency is dominated by CPU-bound
prompt processing (prefill); generation throughput slowly degrades as the KV cache
grows. A naive char-count/4 token estimate underestimated real tokens by 30-40% for
Python code (actual ratio ≈2.9 chars/token, not 4).

## Context Window Analysis (Where did the model fail?)

Within 8 files (2,374 real tokens) the model never forgot the planted constant —
it answered "47, 01_models.py" correctly every time. Padding the prompt with
unrelated filler (16.5K, 35.5K, and 64K characters) forced a failure:
`prompt_eval_count` stayed pinned at **exactly 2,050 tokens** regardless of how much
text was sent. Ollama was silently truncating every prompt to ~2,048 tokens — the
legacy default — regardless of the model's advertised 131,072-token capacity, because
`num_ctx` was never explicitly set. Truncation drops the *oldest* tokens first, so
file 1 (and the constant) was the first casualty once total input passed ~2K tokens.
At the smallest padding level the model honestly admitted it couldn't find the
constant; at larger padding levels it began confabulating a source location instead —
a shift from honest refusal toward mild hallucination as more irrelevant context piled
on.

A second finding fell out of this test: once the trailing (surviving) portion of the
prompt was identical across requests, prompt-eval time dropped from 65.75s to
0.2-0.25s — Ollama reused the KV cache, a ~300x speedup for append-only context growth.
Any edit near the start of a file invalidates that cache and forces full
reprocessing.

## Hybrid Strategy Implementation Plan

**Keep local:** single-file edits, boilerplate/unit-test scaffolding, and quick
lookups that comfortably fit under ~1,500 tokens (headroom below the measured
~2,048-token cliff), especially when the agent loop only appends to a stable prefix
so it benefits from the KV-cache speedup.

**Offload to Claude/GPT-4o:** anything spanning more than 2-3 files, architectural
refactors, or any task where a silent wrong answer is worse than a slow one — the
local model doesn't error on truncation, it just quietly forgets.

**For local tasks that need more context:** explicitly set `num_ctx` (e.g. 8192+)
via the API's `options.num_ctx` instead of trusting Ollama's default, accepting the
added RAM/latency cost that comes with it.

## Future Optimization Steps

- Re-run the padded test with `num_ctx` explicitly raised (4096 / 8192 / 16384) to
  map the real latency/memory cost of each larger ceiling on this CPU.
- Add an automatic token-budget check to the harness that routes a request to a
  cloud model the moment it would exceed a safe local threshold, instead of letting
  Ollama truncate silently.
- Test `OLLAMA_NUM_THREADS` tuning or a smaller/faster quantization for throughput
  gains on this 10-core CPU, since no GPU acceleration path exists on this machine.
