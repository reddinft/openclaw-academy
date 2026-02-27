# Lessons Learned

This is the lesson we wish someone had written before we started. After weeks of running OpenClaw in production on a Mac Mini M4 — with 5 agents, a custom evaluation system, Ollama shadow testing, and daily cron jobs — here's everything that surprised us, broke us, or cost us time and money.

These are grouped into three categories: infrastructure, evaluation system, and budget management.

---

## Infrastructure Lessons

### 1. Your Mac Sleeps and Nobody Tells You

macOS default power settings are designed for laptops. The default `sleep` value on a fresh Mac Mini can put the machine to sleep after an hour of idle. When it sleeps:

- The network goes down (if `networkoversleep` is off, which it is by default)
- Every incoming message is silently dropped
- No error, no log, no notification

We discovered this when a Telegram message went unanswered for hours. The Mac Mini had been sleeping 29 times since last reboot.

**Fix:** A `caffeinate -s -i` LaunchAgent with `KeepAlive: true`. Check with:

```bash
pmset -g assertions | grep caffeinate
```

If you don't see a caffeinate assertion, your machine is sleeping.

> **Key Takeaway:** The first LaunchAgent you install should be caffeinate. Before the Gateway, before anything else. A sleeping server is a dead server that looks alive.

---

### 2. `launchctl setenv` Is a Trap

If your LaunchAgent plist has its own `EnvironmentVariables` block, `launchctl setenv` does nothing. The two environments don't merge. The process only sees what's in its own plist block.

We spent a full day debugging why the gateway couldn't see a 1Password service account token that was clearly set in the shell session.

**Fix:** Bake secrets directly into the plist:

```bash
/usr/libexec/PlistBuddy -c \
  "Add :EnvironmentVariables:MY_SECRET string $VALUE" \
  ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

Then `launchctl unload` + `launchctl load`.

---

### 3. TCC Ties Permissions to Binary Paths

macOS TCC (Transparency, Consent, and Control) ties disk access permissions to the **exact binary path**. Switching from:

```
/opt/homebrew/Cellar/node@24/24.14.0/bin/node
```

to:

```
~/.nvm/versions/node/v24.14.0/bin/node
```

looks identical to you. macOS treats them as completely different programs. The gateway silently loses all its file access permissions.

Getting permissions back requires **interactive approval at the physical machine**. Not remotely. Not via SSH.

**Fix:** Lock your gateway plist to one Node binary path. Never switch between NVM and Homebrew for the daemon binary. If you upgrade Node and the Cellar path changes, check TCC.

---

### 4. Syntax Errors in LaunchAgent Scripts Fail Silently

A Python `IndentationError` in a LaunchAgent-managed script causes exit code 256. If the crash happens before your logging initializes, there's zero trace in the logs.

We had a typo in the shadow accumulator. The LaunchAgent fired every 20 minutes, exited with 256 every time, and we didn't notice for 6 hours. Lost 18 accumulated runs.

**Fix:** Two things:

```bash
# 1. Verify syntax before committing
python3 -c "import run_accumulate"
```

```python
# 2. Log startup as the absolute first line
import logging, os
logging.basicConfig(level=logging.INFO, ...)
logging.info("starting (pid=%d)", os.getpid())
```

If you don't see that startup line in the logs, the crash happened before your code ran.

---

### 5. Non-Admin Users and Homebrew Don't Mix

Running under a standard (non-admin) macOS user is good security. But `/opt/homebrew/Cellar` is owned by the admin account, and `brew install` fails with permission errors.

**Workaround:** Use static binaries from GitHub Releases. Drop them in `~/.local/bin`:

```bash
curl -L https://github.com/example/tool/releases/latest/download/tool_Darwin_arm64.tar.gz \
  | tar -xz -C ~/.local/bin
```

This worked for `jq`, `rg`, `ffmpeg`, `himalaya`, `blogwatcher`, and several others. For tools that genuinely need Homebrew (like some TTS engines), you need the admin to install them.

---

### 6. Python 3.14 Breaks Things You Don't Expect

We chose Python 3.14.3 for the latest stable. Cost: Pydantic V1's `BaseSettings` is gone. Chroma 1.5.1 fails at import. `qdrant-client` 1.17.0 removed `client.search()` (replaced with `client.query_points()`).

**Fix:** Check your key dependencies against your Python version before committing to either. We ended up:
- Replacing Chroma with a numpy cosine store (which was actually better — same embedding space as the evaluation scorer)
- Pinning qdrant-client API usage to `query_points()`
- Testing imports before deploying

---

### 7. Free-Tier APIs Quietly Corrupt Data

Voyage AI's free tier capped at 3 RPM and 10K TPM. When embedding calls fail, the fallback (TF-IDF cosine similarity) produces numerically different scores. If you're not tagging which backend produced each score, you end up with a mixed dataset and no way to separate it.

**Fix:**
1. Add a payment method before collecting data you care about
2. Tag every run with the backend source
3. Build fallbacks that produce comparable (or at least identifiable) scores

> **Key Takeaway:** Any external API with rate limits is a **data quality risk** in an evaluation system, not just a performance one.

---

## Evaluation System Lessons

These came from building the Hybrid Control Plane — our system for shadow-testing local models against Claude.

### 8. None Is Not Zero

When a judge run isn't sampled (we sample at 15% to save costs), the score should be `None`, not `0.0`. Storing `None` and excluding it from the rolling mean is correct. Storing `0.0` poisons the statistics — every unsampled run drags the mean toward zero.

```python
# WRONG: 0.0 poisons the mean
score = judge_result if judge_result else 0.0

# RIGHT: None is excluded from aggregation
score = judge_result  # None if not sampled
scores = [s for s in all_scores if s is not None]
mean = sum(scores) / len(scores) if scores else None
```

---

### 9. Evaluate Your Evaluator First

Our default evaluation weights were 25% structural accuracy, 25% semantic similarity, 20% factual drift, 15% task completion, 5% latency, 10% tool call correctness. These worked great for classification and formatting tasks.

For prose analysis tasks, every model scored 0.44–0.59. All of them. We thought the models were terrible at analysis. They weren't — the evaluator was wrong.

**Root cause:** `difflib.SequenceMatcher` on prose gives ~0.29 even for semantically equivalent text. At 25% weight, this capped the structural score at ~0.29, dragging the overall score below 0.60 no matter how good the semantic match was.

**Fix:** Per-task weight overrides:

| Task type | Structural | Semantic | Other weights |
|-----------|-----------|----------|---------------|
| classify, format, extract | 25% | 25% | Default |
| analyze, summarize | 10% | 40% | Adjusted |

Post-fix: analyze mean went from 0.59 to 0.70, with 7/10 runs above the floor.

> **Key Takeaway:** A suspicious ceiling across ALL models means the metric is wrong, not the models. If every candidate scores the same, your evaluator has a bottleneck.

---

### 10. Constrain the Output Format

When comparing Claude's ground truth against a local model's output, format drift kills scores. If Claude writes in paragraphs and the candidate writes in bullet points, the structural similarity plummets even if the content is identical.

**Fix:** Constrain both ground truth and candidate to the same output format via the system prompt:

```
Output format:
- Finding: [one sentence]
- Recommendation: [one sentence]
- Confidence: [high/medium/low]
- Reasoning: [brief explanation]
```

This dramatically reduced Layer 2 (structural) drift penalty.

---

### 11. Strip Thinking Tokens

Chain-of-thought models (DeepSeek-R1, reasoning models) wrap their output in `<think>...</think>` tags. If you evaluate with the thinking tokens included, the structural evaluation fires on the reasoning chain — which was never meant to be compared.

**Fix:** Strip `<think>...</think>` before evaluation:

```python
import re
output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
```

---

### 12. Judge Sampling Saves More Than You Think

Running the judge (Opus) on 100% of evaluation runs costs more in API fees than you save by routing locally. At 15% sampling, you get statistically valid scores with a fraction of the cost.

The math: if judging each run costs $0.02 and you run 100 tasks/day, that's $2/day just for evaluation. At 15% sampling, it's $0.30/day. Over a month, that's $51 saved.

---

## Budget Management Lessons

### 13. Start with Sonnet, Not Opus

We initially ignored the setup wizard's advice and ran Opus for everything. It got expensive within days. The fix was obvious in retrospect:

| Task | Model | Why |
|------|-------|-----|
| Planning, judging, architecture | Opus 4.6 | Needs highest quality |
| Routine chat, cron jobs, heartbeat | Sonnet 4.6 | Fast, cheap, good enough |
| Shadow testing, experiments | Ollama (local) | Free |

**Rule:** Never spend Opus tokens on a task Sonnet can handle. And never spend Sonnet tokens on a task a local model can handle (once promoted).

### 14. Track Everything to Langfuse

Self-hosted Langfuse (free, Docker Compose) gives you:
- Token usage per model, per task, per agent
- Latency tracking
- Error rates
- Cost attribution

Without observability, you're guessing where money goes. With it, you can identify the exact tasks consuming the most tokens and target those for optimization.

### 15. The Fallback Chain Is a Budget Feature

Our fallback chain isn't just for reliability:

```
Opus 4.6 → Sonnet 4.6 → GPT-4.1 → Ollama qwen2.5
```

When Anthropic has an outage, the agent doesn't stop working — it falls back to GPT-4.1. This prevents the scenario where you're paying for an always-on server that can't do anything because one provider is down.

---

## The Meta-Lesson

The hardware is the easy part. A Mac Mini M4 with 24GB unified memory is good hardware for this. We run 10 Ollama models and the ones that fit in memory are fast enough.

The hard part is everything around it:
- macOS daemon assumptions that don't match persistent AI services
- Evaluation metrics that silently produce wrong scores
- Data quality degradation from API rate limits
- Cost tracking that requires disciplined observability

None of these problems are exotic. Every one has a documented fix. The issue is they don't announce themselves — they show up as "why isn't this working?" or, worse, "why does the data look slightly off?"

---

## The Checklist

If you're building a similar setup, check these before you go live:

```
Infrastructure:
[ ] caffeinate LaunchAgent running
[ ] pmset -g shows sleep prevented
[ ] All env vars baked into plist (not launchctl setenv)
[ ] Node binary path locked (check after upgrades)
[ ] Log startup as first line of every daemon script
[ ] Python dependency versions checked against Python version
[ ] API payment methods added before collecting evaluation data

Evaluation:
[ ] None vs 0.0 handled correctly for unsampled runs
[ ] Per-task weight overrides configured (not default for all)
[ ] Output format constrained for both ground truth and candidates
[ ] Thinking tokens stripped from CoT models
[ ] Judge sampling rate set (15% is a good starting point)
[ ] Score distributions checked per task type (look for suspicious ceilings)

Budget:
[ ] Opus reserved for judgment and architecture only
[ ] Sonnet for routine tasks
[ ] Ollama for shadow testing and experiments
[ ] Langfuse tracking all token usage
[ ] Fallback chain configured for provider outages
[ ] Monthly cost reviewed against actual usage
```

---

## Summary

| Category | Lesson | Impact |
|----------|--------|--------|
| Infra | Mac sleeps silently | Lost messages for hours |
| Infra | `launchctl setenv` ignored | Full day debugging |
| Infra | TCC binary path lock | Silent permission loss |
| Infra | Silent LaunchAgent failures | 6 hours, 18 lost runs |
| Infra | Homebrew needs admin | Blocked installs |
| Infra | Python 3.14 breaks Pydantic V1 | Replaced Chroma entirely |
| Infra | Free-tier API rate limits | Corrupted evaluation data |
| Eval | `None != 0.0` | Poisoned rolling statistics |
| Eval | Default weights wrong for prose | All models scored ~0.5 |
| Eval | Format drift kills scores | Constrain output format |
| Eval | Thinking tokens in eval | False structural failures |
| Eval | 100% judge sampling too expensive | 15% is enough |
| Budget | Opus for everything | Expensive in days |
| Budget | No observability | Couldn't track spend |
| Budget | No fallback chain | Provider outage = downtime |

---

## Exercise

1. Review your own daemon/service setup. Is anything sleeping? Is `caffeinate` (or equivalent) running?
2. Check your evaluation metrics for suspicious patterns — are all models scoring in a narrow band? That's a metric problem, not a model problem.
3. Set up Langfuse (self-hosted, Docker Compose) and instrument one LLM call with token tracking
4. **Bonus:** Write a cost projection for your setup based on 30 days of expected usage

---

This wraps up the OpenClaw Academy course. You've gone from "what is OpenClaw?" to deploying, extending, and operating a production multi-agent system. The next step is yours — build something, break something, learn something, and share what you find on ClawHub.
