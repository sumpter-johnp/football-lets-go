# Project Sideline — Opponent Intelligence Engine

*A build outline and delivery plan. Working name: Sideline (rename at will).*

---

## The goal

Build an engine that produces a weekly, automated **opponent intelligence brief** for BYU football, and hand the first one to the coaching staff ahead of early-season prep — with the flagship edition targeting the **September 12 home game vs. Arizona**.

The engine does the digging; the coaches keep the judgment. This is explicitly *not* a game-plan generator. It surfaces asymmetries — where the opponent is predictable, where their coaching staff's history reveals tendencies, and where those weaknesses intersect with BYU's strengths — and presents them in a format a quality-control analyst or position coach can act on.

**Success looks like:** a coach reads the brief, finds one thing they didn't already know or hadn't quantified, and asks for the next week's edition. That's it. If they already have everything in it, the fallback outcome is still a complete portfolio project demonstrating data pipelines, statistical modeling, and LLM orchestration end to end.

---

## Why this might work (and the honest case against)

**For:**

- The revenue-share era is forcing programs to build NFL-style analytics operations, but most staff attention goes to *player evaluation* (recruiting, portal). Weekly opponent intelligence is still largely manual quality-control labor.
- The **coach DNA** angle is underserved: rosters turn over annually now, but coordinators carry their tendencies across jobs. When an opponent has a new coordinator, last season's film on that team is nearly worthless — the coordinator's multi-year history at previous stops is the predictive signal, and assembling it is a data-pipeline problem, not a scheme-expertise problem.
- The artifact is self-demonstrating. A brief about *their* week-2 opponent, delivered the week they're preparing for it, answers a question they are actively working on.

**Against (know these going in):**

- BYU already subscribes to professional tools (Hudl-class film/data platforms, scouting data services) with charting data this engine can't access.
- Public play-by-play has **no formations, personnel groupings, or coverages**. The engine's ceiling is situational tendencies, not schematic detail.
- Coaches self-scout; strong tendencies are sometimes bait. The brief must report sample size and stability alongside every tendency, or it loses credibility with the first skeptical coordinator who reads it.

---

## Architecture

Four layers, matching the flow: data → analysis → matchup → brief.

### 1. Data layer

| Source | Contents | Access |
|---|---|---|
| CollegeFootballData API / `cfbfastR` | Play-by-play back to ~2014, EPA/success rate, drives, game state | Free API key |
| Coaching staff database (built by us) | Every FBS coordinator and head coach, career stops with years, linked to team-seasons | Scraped/compiled from public records (school sites, Wikipedia, news) |
| Rosters, portal, injuries | Depth charts, transfer activity, availability | CFBD rosters + news scraping |
| Unstructured media | Press conferences, articles, coach biographies/books, podcasts | Web scraping + transcripts; summarized by LLM |

All of it lands in Supabase (Postgres) — same stack as project-homebase. Tables roughly: `teams`, `coaches`, `coach_stints` (coach × team × role × years), `games`, `plays` (with EPA and situation fields), `players`, `media_items`.

### 2. Tendency engine

Deterministic SQL/Python over the plays table. Per team-season *and* per coordinator:

- Run/pass rate by down × distance × field position × score state × time
- Pace (seconds per snap) by game state
- Aggression: 4th-down go rate vs. expected, 2-point behavior, deep-shot rate
- Red-zone identity, short-yardage identity, opening-script behavior (first 15 plays)
- Blitz/pressure *proxies* (sack rates, TFL rates, havoc allowed — honest about being proxies)
- **Predictability score**: for each situation bucket, how far the team deviates from league-average mixing. High predictability = exploitable; report it with sample size and cross-season stability.

### 3. Coach DNA profiles

The differentiated piece. Join `coach_stints` to `plays` so every play is attributed to the coordinator who called that unit. Then:

- Build tendency profiles **per coach across their whole career**, not per team
- Test persistence: does a coordinator's 3rd-and-medium behavior at stop N predict stop N+1? (This is the riskiest assumption in the project — validate it first; see Phase 0.)
- When an opponent hires a new coordinator, generate their profile from prior stops and flag which old-team film is most representative
- Layer in the qualitative record: what the coach has said in pressers/books/articles about philosophy, tempo, risk. LLM-summarized with citations back to sources.

### 4. Matchup model + weekly brief

- Intersect opponent's worst situations (EPA allowed, by bucket) with BYU's best (EPA gained) → ranked list of the week's highest-leverage asymmetries, and the mirror image (their strengths vs. our weaknesses = threats)
- LLM synthesis layer assembles the brief: numbers → prose + charts, plus the media digest (injuries, presser notes, staff changes)
- Output: a PDF/web report, 6–10 pages, generated by pipeline, reviewed by a human (me) before it goes anywhere

---

## The brief — table of contents (v1)

1. **One-page summary** — five bullets a head coach could read in 90 seconds
2. **Opponent identity** — offensive and defensive tendency profile, predictability scores, what's stable vs. noisy
3. **Coach DNA** — coordinator career profiles, philosophy notes from the public record, what changed since their last stop
4. **How they may attack BYU** — their strengths mapped onto BYU's statistical weaknesses (threats)
5. **Where BYU's leverage is** — BYU strengths mapped onto their statistical weaknesses (opportunities)
6. **Situational appendix** — 4th-down/2-pt profiles, red zone, pace, opening scripts, with sample sizes on everything
7. **Personnel notes** — portal additions/losses, injury status, depth chart changes (clearly sourced)

Every claim carries its sample size and a stability flag. No play calls, no scheme recommendations — asymmetries only.

---

## Build phases

**Phase 0 — Validate the core assumption (1 weekend).**
Test whether coordinator tendencies persist across jobs *before building anything else*. The design is an out-of-sample backtest with a built-in natural experiment:

- **Train/test split**: predict from career-through-2024 data, evaluate against actual 2025 behavior. Never test against a single game (~70 plays sliced into situation buckets is pure noise, contaminated by game script) — the unit of validation is the coordinator's full-2025 profile, aggregated across all games.
- **Situation-neutral filter**: restrict to one-score games, quarters 1–3, to strip out scoreboard-driven behavior. A team down 21 passes because of the score, not the coach.
- **The natural experiment**: the test set is coordinators who *changed schools* between 2024 and 2025 (pull the list from the CFBD coaches endpoint, not memory). For each mover there are two competing predictors of the new team's 2025 behavior:
  - (a) the coach's tendency profile from his old stops, vs.
  - (b) the new team's prior-year profile under its previous coordinator.

  If (a) predicts better than (b), tendencies follow the coach and coach DNA is real. If (b) wins, program/roster identity dominates and the layer demotes to nice-to-have. Coordinators who stayed put can't answer this — coach and team are confounded.
- **Test sticky metrics only**: early-down neutral pass rate, pace (seconds per snap), 4th-down aggression relative to situation, and shot-play rate. Skip personnel-hostage metrics (e.g., red-zone rushing TD share measures the running back, not the coordinator). Partial persistence is still a win — it defines which dials the DNA profile can honestly claim to read.
- **Output**: one CSV — one row per mover, columns for predictor (a) error, predictor (b) error, per metric — plus a short written verdict.

**Phase 1 — Data foundation (2–3 weeks of evenings).**
CFBD ingestion into Supabase; plays table with situation fields and EPA. Coach stints table for Big 12 staffs + BYU's 2026 opponents only (don't boil the ocean — ~15 teams covers the season).

**Phase 2 — Tendency engine (2 weeks).**
Situation-bucket queries, predictability scoring, cross-season stability checks. Output as clean JSON per team/coach.

**Phase 3 — Matchup + brief generation (2 weeks).**
BYU-vs-opponent intersection logic; report template; LLM synthesis with charts (charting via a simple plotting pipeline); human review pass.

**Phase 4 — The Arizona edition (game week).**
Utah Tech (Sept. 5, FCS) is a poor analytics target — FCS data coverage is thin and the game is a mismatch. Produce a *light* week-1 edition as a dress rehearsal, then ship the full flagship brief for **Arizona (Sept. 12)**: returning veteran QB, divisional stakes, rich Big 12 data, and BYU's staff has beaten this program five straight — meaning Arizona's staff will be scheming change, which is exactly what coach DNA is for.

Total: roughly 6–8 weeks of nights and weekends, timed to finish by late August.

---

## Delivery plan

Not a cold pitch — a warm artifact.

1. **Route in through the network**: BYU's sports-analytics student community, the Marriott School's athletics connections, and any one-hop intros to football staff (personnel/quality-control side, not the head coach).
2. **Lead with the document, not a deck**: send the Arizona brief itself with a two-line note: built this as a personal project, thought it might be useful for week 2, happy to produce it weekly if any of it lands.
3. **Expect and welcome "we already have this"**: the follow-up question is *which parts* they already have — that conversation is the real market research, and it's how a student-analyst role gets created.
4. **Information hygiene**: everything in the brief is from public data and public statements. Nothing proprietary, nothing scraped from paid tools, sources cited. This matters to a program's compliance instincts and to the credibility of the work.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Coach tendencies don't persist across jobs | Phase 0 backtests 2025 movers out-of-sample first; project reweights if the prior-team baseline wins |
| Staff already has everything via paid tools | Coach DNA + media synthesis are the least-covered pieces; also, fallback value is the portfolio |
| Tendencies are self-scouted bait | Report stability + sample size on every claim; frame as "where film study pays off," not "what they'll do" |
| Public data too coarse for credibility | Stay in the situational lane; never fake schematic precision the data doesn't support |
| Time collides with internship/MBA | Phases are independently shippable; Phase 0 + 1 alone produce a usable tendencies database |

---

## Stack

Python-first, no frontend. Infrastructure is added only when a phase demands it:

- **Phase 0**: Python + pandas + CFBD API key only. No database, no deploy — it's a research script that outputs a CSV and a verdict.
- **Phases 1–2**: Add **Supabase (Postgres)** as the data warehouse. Ingestion and transformation run from Python (`supabase-py` or SQLAlchemy/psycopg) — same pattern as a small data warehouse project: ingest scripts, tables, transformation queries.
- **Phase 3**: Still Python. The brief is a *document*, not an app — markdown + matplotlib/plotly charts rendered to **PDF**. A PDF is the right deliverable for a coaching staff: printable, forwardable, no login.
- **Scheduling**: manual runs (one opponent per week, Sunday night) are fine for a full season. Automate later with a GitHub Actions cron or Supabase `pg_cron` if wanted.
- **Claude API** for the media digest and brief synthesis (Phase 3).
- **Not in scope**: Next.js/Vercel/frontend. Only earns its way in later if an interactive tendency explorer or web version of the brief becomes worth having.

Suggested repo layout: one repo with `ingest/`, `analysis/`, and `report/` directories.
