# OpenClaw Academy — QC Review

**Reviewer:** Community QC
**Date:** 2026-02-27
**Scope:** All 10 modules, 33 lessons, 10 quizzes

---

## 1. Executive Summary

**Overall Quality Score: 4/10**

The academy has a strong foundation in Module 1 but is fundamentally incomplete. Only 1 of 10 modules has actual content — the remaining 9 are placeholder stubs with "coming soon" notices. The complete module (Module 1) is well-written and largely accurate, making it a good template for the rest.

### Top 3 Issues

1. **90% of content is stubs** — Modules 2–10 have zero educational content. Each lesson is just a bullet list of "what to expect." This is not a course; it's a course outline with one finished chapter.
2. **9 of 10 quizzes are broken placeholders** — Modules 2–10 have identical single-question "coming soon" quiz files with malformed IDs (`mmodule-quiz` instead of proper IDs like `m02-quiz`).
3. **Minor inaccuracies in Module 1** — iMessage integration method, some channel listings, and a few technical details need correction against actual docs.

---

## 2. Per-Module Review

### Module 1: OpenClaw Overview
- **Accuracy:** 8/10
- **Completeness:** ✅ Complete
- **Voice & Tone:** Excellent — conversational, clear, well-structured with tables, diagrams, and exercises

**Key Issues:**

1. **iMessage description is inaccurate.** Lesson 1 says "iMessage (macOS, via AppleScript)". The actual docs show iMessage uses **BlueBubbles** (recommended, REST API) or **imsg** (legacy, JSON-RPC over stdio). AppleScript is not the integration method.
   - **Fix:** Change to "iMessage (macOS, via BlueBubbles)" or "iMessage (macOS, via BlueBubbles / imsg)"

2. **Channel list has omissions and extras.** Lesson 1 lists "iOS node" and "Android node" as channels — these are **nodes**, not channels (the lesson even defines nodes separately). Meanwhile, several real channels are missing: LINE, Nostr, Tlon, Twitch, Zalo, Nextcloud Talk, Synology Chat, Feishu, BlueBubbles.
   - **Fix:** Separate nodes from channels. Add missing channels or note "and more via plugins."

3. **Discord library name needs context.** Course says "Discord (via Carbon)" — this is technically correct (@buape/carbon is a dependency) but the docs also reference @discordjs/voice for voice features. The description is acceptable but could note this.

4. **Session key format in Lesson 2.** The example session key `agent:main:telegram:dm:123456789` is used, but the actual docs describe DMs collapsing to `agent:<agentId>:<mainKey>` (default `main`) when `dmScope` is `"main"` (the default). The per-channel-peer format shown would only apply with `dmScope: "per-channel-peer"`. The lesson conflates these.
   - **Fix:** Clarify that with default `dmScope: "main"`, all DMs share the session key `agent:main:main`. The channel-specific key format applies with other dmScope settings.

5. **Step 4 in Lesson 3 (End-to-End Flow)** says with `dmScope: "main"` the session key is `"agent:main:main"` — this is actually **correct** per the docs. But Step 6 in the same lesson references `agent:main:telegram:dm:123456789` in the session key section of Lesson 2, creating an inconsistency between lessons.
   - **Fix:** Make Lesson 2 and Lesson 3 consistent. Lesson 2's architecture overview should note both formats.

6. **"Express" mentioned in architecture table.** Lesson 2 says "Node.js, Express, WS" for the Gateway. There's no indication in the docs that Express is used — the gateway uses its own HTTP/WS server. This may be inaccurate.
   - **Fix:** Verify whether Express is actually used. If not, change to "Node.js, WS" or "Node.js, HTTP, WS".

7. **Mattermost listed as "plugin" in the channel table but as built-in in the list.** The docs show Mattermost as a plugin installed separately, which matches. But the channel table in Lesson 2 doesn't mention it's a plugin.

8. **Minor: "Node.js ≥22" in summary table.** Verify minimum Node version against actual requirements.

**Quiz (Module 1):**
- **Quality: 8/10** — Good questions testing understanding, not just recall
- Question 4 (pairing behavior) is well-crafted with plausible distractors
- Question 6 (session definition) tests conceptual understanding
- All explanations are helpful and add context
- 70% passing score (5/7) is appropriate
- **Issue:** Quiz ID `m01-quiz` is properly formatted ✅

---

### Module 2: Gateway Architecture
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 4 lessons, each is a "coming soon" placeholder with bullet list of planned topics
- **Quiz:** Placeholder with malformed ID `mmodule-quiz`, single dummy question

### Module 3: Channel System
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical to Module 2's)

### Module 4: Agent System
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 4 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 5: Skills & Hooks
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 6: Security Model
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 7: Configuration Deep Dive
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 4 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 8: Extending OpenClaw
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 9: Deployment Patterns
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

### Module 10: Case Study
- **Accuracy:** N/A (no content)
- **Completeness:** 🔴 Stub
- **Content:** 3 lessons, all "coming soon" placeholders
- **Quiz:** Placeholder (identical)

---

## 3. Quiz Review

| Module | Status | Questions | Quality | Issues |
|--------|--------|-----------|---------|--------|
| 1 | ✅ Complete | 7 | 8/10 | Minor: could add 1-2 harder questions |
| 2 | 🔴 Placeholder | 1 (dummy) | 0/10 | Malformed ID: `mmodule-quiz` should be `m02-quiz` |
| 3 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same malformed ID issue |
| 4 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 5 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 6 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 7 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 8 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 9 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |
| 10 | 🔴 Placeholder | 1 (dummy) | 0/10 | Same |

**All 9 placeholder quizzes have the same bug:** quiz ID is `mmodule-quiz` (literal string "module" instead of the module number). This looks like a template expansion failure.

---

## 4. Structural Issues

### What Works
- **Module ordering is logical.** Overview → Gateway → Channels → Agents → Skills → Security → Config → Extending → Deployment → Case Study is a sensible progression.
- **Module 1 sets the right tone.** It successfully introduces all key concepts before they're needed in later modules.
- **The outline is comprehensive.** The planned topic list for each module covers the right ground.

### Gaps & Problems
1. **Modules 2 and 7 overlap significantly.** Module 2 Lesson 4 is "Configuration System" and Module 7 is entirely "Configuration Deep Dive." The outline acknowledges this somewhat, but the boundary is unclear. Consider: Module 2 covers config basics, Module 7 covers advanced patterns.
2. **No "Getting Started" / hands-on module.** There's no module for actually installing and running OpenClaw. Module 1 mentions installation but doesn't walk through it. Module 9 (Deployment) comes too late — learners should set up OpenClaw early so they can follow along.
3. **Missing prerequisite declarations.** No module declares what prior modules are required. The meta.yaml files weren't examined in detail but should contain this.
4. **No progressive exercises.** Module 1 Lesson 3 has one exercise (look at your session transcript). The stubs don't mention exercises. A course needs hands-on work.
5. **Module 10 (Case Study) references personal setup details** (Mac Mini, Tailscale, QMD, Proton Drive). This is valuable as a real example but may confuse learners who think these are required components.

---

## 5. Priority Fix List

Ranked by impact:

| # | Priority | Fix | Effort | Impact |
|---|----------|-----|--------|--------|
| 1 | 🔴 Critical | **Write Module 2 content** (Gateway) — this is the next logical module and unblocks understanding of everything else | High | Enables learning progression |
| 2 | 🔴 Critical | **Write Module 4 content** (Agents) — the agent system is what users interact with most | High | Core understanding |
| 3 | 🟡 High | **Fix all placeholder quiz IDs** — change `mmodule-quiz` to `m02-quiz`, `m03-quiz`, etc. | Trivial (5 min) | Prevents bugs in any quiz system |
| 4 | 🟡 High | **Write Module 5 content** (Skills) — skills are the main extensibility mechanism | High | Practical value |
| 5 | 🟡 High | **Fix Module 1 inaccuracies** — iMessage description, channel list cleanup, session key consistency | Low (30 min) | Accuracy for the one complete module |
| 6 | 🟠 Medium | **Write Module 9 content** (Deployment) — or move a "Quick Start" section earlier | High | Hands-on setup |
| 7 | 🟠 Medium | **Write Module 6 content** (Security) — security understanding is important before extending | High | Safety |
| 8 | 🟠 Medium | **Add a "Getting Started" module** or move installation into Module 1 | Medium | Learner onboarding |
| 9 | 🔵 Low | **Write Modules 3, 7, 8** — channels, config deep dive, extending | High | Completeness |
| 10 | 🔵 Low | **Write Module 10** (Case Study) — nice-to-have, not blocking | Medium | Real-world context |

---

## Summary

Module 1 is a genuinely good piece of educational content — well-structured, appropriately detailed, with good diagrams and a solid quiz. It proves the format works. But 90% of the course is empty scaffolding. The most urgent need is simply writing content for the remaining modules, using Module 1 as the quality bar. The few inaccuracies in Module 1 are minor and easily fixed.

**Bottom line:** Great outline, great template in Module 1, but this is a course skeleton, not a course.
