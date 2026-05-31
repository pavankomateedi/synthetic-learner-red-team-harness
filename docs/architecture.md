# Architecture & Capability Map — one-pager

> **What this is:** a red-team harness that stress-tests an AI fractions tutor
> with 10 research-grounded synthetic students, surfaces educational failure
> modes, runs one recursive improvement cycle (V1 → V2), and guards against
> benchmark gaming. Fully deterministic (seeded), runs offline, no API key.

---

## Capability map — who can do what

```mermaid
flowchart LR
  classDef aud fill:#1c1b18,stroke:#67e8f9,color:#67e8f9;
  classDef cap fill:#141729,stroke:#272a44,color:#f0f4ff;
  classDef sys fill:#231a4a,stroke:#a78bfa,color:#a78bfa;

  Eng["👷 Engineering<br/>(Nerdy product team)"]:::aud
  Tch["🍎 Teachers"]:::aud
  Par["👨‍👩‍👧 Parents"]:::aud
  Dev["🔧 System owner<br/>(extend the harness)"]:::aud

  C1["Headline V1↔V2 comparison<br/>(7 dims + deltas)"]:::cap
  C2["Per-persona heatmap<br/>(10 student types)"]:::cap
  C3["Counter-metrics<br/>(anti-gaming checks)"]:::cap
  C4["Where V2 falls short<br/>(failures + regressions)"]:::cap
  C5["Raw JSON snapshot<br/>(metrics.json)"]:::cap
  C6["Reproducible local eval<br/>(slh run / compare)"]:::cap
  C7["Pedagogical practices<br/>the tutor adopts"]:::cap
  C8["Plain-language outcomes<br/>(no metric jargon)"]:::cap
  C9["Honest 'still struggles'<br/>narrative"]:::cap

  S1["Add personas / tutors / problems"]:::sys
  S2["Add golden-set checks<br/>(26 gates)"]:::sys
  S3["Add evaluation dimensions"]:::sys
  S4["Add a new audience view"]:::sys

  Eng --> C1 & C2 & C3 & C4 & C5 & C6
  Tch --> C7 & C4 & C2
  Par --> C8 & C9
  Dev --> S1 & S2 & S3 & S4
```

---

## Architecture — modules, data flow, deployment

```mermaid
flowchart TB
  classDef dom fill:#1c1b18,stroke:#67e8f9,color:#f0f4ff;
  classDef eng fill:#141729,stroke:#a78bfa,color:#f0f4ff;
  classDef ev  fill:#231a4a,stroke:#f472b6,color:#f0f4ff;
  classDef out fill:#0b0e1f,stroke:#fbbf24,color:#f0f4ff;
  classDef dep fill:#191c33,stroke:#34a853,color:#f0f4ff;

  subgraph Domain["DOMAIN MODEL · what is being tested"]
    Curr["curriculum.py<br/>17 fraction problems<br/>5 documented misconceptions"]:::dom
    Pers["personas.py<br/>10 archetypes<br/>(incl. 2 negative-result)"]:::dom
    Prot["protocol.py<br/>Move / Action / Turn / ItemState"]:::dom
  end

  subgraph Engine["SIMULATION ENGINE · seeded, deterministic"]
    Learn["learner.py<br/>SyntheticLearner agent<br/>memory + decision policy"]:::eng
    Tut["tutor.py<br/>TutorV1 (flawed) +<br/>TutorV2 (improved)"]:::eng
    Sess["session.py<br/>multi-turn loop<br/>+ pre/post assessment"]:::eng
  end

  subgraph Eval["EVALUATION · 7 dims + 5 counter-metrics + 26 gates"]
    Det["detectors.py<br/>avoidance / shallow-compliance / recovery"]:::ev
    Evtr["evaluator.py<br/>aggregate + per-persona scoring"]:::ev
    Cmp["comparator.py<br/>V1→V2 deltas + regressions + counter-metrics"]:::ev
    Gold["goldenset.py<br/>26 checkable expectations<br/>(intent contract)"]:::ev
  end

  subgraph Output["PRESENTATION · same data, 3 audiences"]
    Hrn["harness.py<br/>orchestrates the loop"]:::out
    Rpt["report.py<br/>failure + comparison Markdown"]:::out
    Web["web.py<br/>FastAPI app: /, /teacher.html, /parents.html"]:::out
    CLI["cli.py<br/>slh check / run / compare"]:::out
  end

  subgraph Deploy["DEPLOY · GitHub Pages, free, public, reversible"]
    Build["scripts/build_static.py<br/>renders 3 HTML files"]:::dep
    GH["github.com/pavankomateedi/<br/>synthetic-learner-red-team-harness"]:::dep
    Pages["pavankomateedi.github.io/<br/>synthetic-learner-red-team-harness/"]:::dep
  end

  Curr --> Learn
  Curr --> Tut
  Pers --> Learn
  Prot --> Learn
  Prot --> Tut
  Learn --> Sess
  Tut --> Sess
  Sess --> Det
  Sess --> Evtr
  Det --> Evtr
  Evtr --> Cmp
  Cmp --> Gold
  Cmp --> Rpt
  Cmp --> Web
  Hrn --> Sess
  Hrn --> Evtr
  Hrn --> Cmp
  CLI --> Hrn
  Web --> Build
  Build --> GH
  GH -->|auto Pages build| Pages
```

---

## Module quick-reference

| Module | Responsibility | LOC |
|---|---|---|
| `curriculum.py` | Item bank (instruction / assessment / transfer) + misconception catalog | ~80 |
| `personas.py` | 10 archetypes, each with knowledge / motivation / behavior / memory / avoidance dimensions | ~225 |
| `protocol.py` | Shared types (`Move`, `Action`, `Turn`, `ItemState`, `Transcript`) | ~80 |
| `learner.py` | `SyntheticLearner` per-turn decision engine + memory consolidation | ~175 |
| `tutor.py` | `TutorV1` (flawed baseline) + `TutorV2` (improved) policies | ~165 |
| `session.py` | Multi-turn loop runner + pre/post assessment | ~95 |
| `detectors.py` | Avoidance + shallow-compliance + recovery detection | ~75 |
| `evaluator.py` | 7 PRD §8.1 dimensions, overall + per-persona | ~150 |
| `comparator.py` | V1→V2 deltas, regression check, 5 PRD §8.2 counter-metrics | ~170 |
| `goldenset.py` | 26 checkable expectations (population + comparison + behavior) | ~210 |
| `report.py` | Failure-mode + comparison Markdown renderers | ~125 |
| `harness.py` | Orchestrates the improvement loop | ~40 |
| `web.py` | FastAPI dashboard — 3 audience views (Nerdy / Teachers / Parents) | ~680 |
| `cli.py` | `slh check / run / compare` entrypoint | ~90 |

---

## Quality gates

| Gate | Tool | Target | Current |
|---|---|---|---|
| Lint | `ruff` | clean | ✅ clean |
| Tests | `pytest` | green | ✅ **63 passing** |
| Coverage | `pytest --cov` | ≥ 85 % | ✅ **97.5 %** |
| Golden set | `slh check` | 26/26 | ✅ **26/26** |
| Live URL | `curl` | HTTP 200 | ✅ 200 (×3 pages) |

The golden set is the eval contract — each gate encodes an *intent* that must
keep holding (e.g. *"V2 must withhold answers"*, *"struggling learner must
stay below the transfer threshold — that's intentional"*, *"at least one
honest regression must exist or improvement looks gamed"*). New behaviors
get pinned by adding gates, not by manual review.

---

## Recursive improvement loop

```mermaid
flowchart LR
  classDef step fill:#141729,stroke:#67e8f9,color:#f0f4ff;
  classDef gate fill:#231a4a,stroke:#f472b6,color:#f0f4ff;

  A["1 · Run V1 on<br/>10×25 = 250 sessions"]:::step
  B["2 · Evaluate<br/>(7 dims + per-persona)"]:::step
  C["3 · Failure analysis<br/>(report.py)"]:::step
  D["4 · Author V2<br/>policy fixes"]:::step
  E["5 · Run V2 on<br/>same 250 sessions"]:::step
  F["6 · Compare<br/>(deltas + counter-metrics)"]:::step
  G{"7 · Regression check<br/>+ golden set"}:::gate
  H["Ship V2<br/>(deploy)"]:::step
  I["Revise V2<br/>or revert"]:::step

  A --> B --> C --> D --> E --> F --> G
  G -->|all gates pass| H
  G -->|any gate fails| I
  I --> D
```

---

## Audience views (one URL each)

| Audience | URL path | Lens | What's surfaced |
|---|---|---|---|
| Engineering (Nerdy) | `/` | technical | All 7 dimensions, counter-metrics, falls-short table, per-persona heatmap, failure modes per tutor |
| Teachers | `/teacher.html` | pedagogical | 3 big stats (answer-handing %, misconception-fix %, recovery %), practices the tutor adopts, falls-short table, persona archetypes |
| Parents | `/parents.html` | outcome | 3 plain stats (types helped / answer-handing / types it can't reach), "What it does well", honest "Where it still struggles" |

---

## Why this design

| Choice | Reason |
|---|---|
| Rule-based agents (no LLM in the loop) | Quality gates must be deterministic; PRD §10.2 permits it; failures must be reproducible to be falsifiable |
| Static export to GitHub Pages | Dashboard is fully deterministic — same numbers every run — so a static snapshot is identical to the live FastAPI server, at zero cost |
| Three audience views | Same harness data, three lenses — different vocabulary serves different decision-makers |
| Two intentional negative-result personas | Avoids "all positive results" theater; pins honest failures into the golden set so future changes can't quietly hide them |
| Golden-set checks live in code, not prose | Continuous-improvement requires re-checking against the contract on every change — code is re-runnable, prose decays |
