# True Line — Market Deployment Criteria

**Status:** LOCKED criteria. Apply mechanically. Do not modify post-results without an explicit re-locking commit.
**Date locked:** May 5, 2026
**Author of decision:** Zach (operator)
**Methodology source:** Same pre-commitment discipline used for v1.2.1 validation in `V1_2_1_2025_VALIDATION_PRECOMMITMENT.md`.

---

## What this document does

Defines the criteria a market (Moneyline / Over-Under / Run Line) must meet to be **deployed publicly** under the True Line brand, and the criteria for being **pulled** if live performance regresses.

The point of this doc is to prevent goalpost-moving once results are live. Whatever the live data looks like, this doc tells us what to do without judgment-call wiggle room.

---

## The product

**True Line publishes algorithmic sports picks** with a verifiable track record. Picks come from the v1.2.1 model (see `V1_2_1_OOS_2025_VALIDATION_SUMMARY.md` for backtest validation).

**Selection rule:** Top-1 pick per market per day at 5% edge floor. Markets that don't qualify on a given day produce zero picks for that market.

**Display unit:** All public picks shown in **units (1u = 1 unit)**. This is the standard sports-betting convention for picks services, allowing each customer to scale to their own bankroll. Operator's personal stake size is internal and not part of the public display.

---

## Deployment criteria for INITIAL launch

A market is eligible for live posting if **ALL of these hold** in backtest data (currently April 2024 - August 2025, ~1.5 seasons):

1. **Aggregate ROI > 0%** at top-1-per-day picks (across full backtest period)
2. **Aggregate median CLV > 0%** at top-1-per-day picks
3. **Positive ROI in every individual test half** measured (currently 4 halves: 2024 H1, 2024 H2, 2025 OOS H1, 2025 OOS H2)
4. **Positive CLV in every individual test half** measured
5. **Minimum 250 picks** at top-1-per-day filter across the backtest period

Why these specific thresholds:

- **Per-half consistency (3 and 4)** distinguishes real edge from period-specific variance. A market that's positive 4 of 4 halves has a much lower probability of being a coin-flip than one that averages positive but is inconsistent.
- **250-pick minimum (5)** is the operational floor at current sample sizes. Designed to deploy markets with strong consistency now, with the expectation that the bar tightens as more data accumulates (see "Future tightening" below).
- **Aggregate AND per-half positive** prevents a market from qualifying based on one outlier half pulling up the average.

---

## Markets evaluated as of May 5, 2026

Applied to current backtest data:

| Market | Aggregate ROI | Aggregate CLV | Halves positive ROI | Halves positive CLV | n | Eligible? |
|---|---|---|---|---|---|---|
| Run Line top-1/day | +10.58% | +1.80% | 4 of 4 | 4 of 4 | 251 | **✅ DEPLOY** |
| Moneyline top-1/day | -9.44% | +3.70% | 0 of 4 | 4 of 4 | 376 | ❌ ROI fails |
| Over/Under top-1/day | +2.50% | +0.00% | (mixed) | 0 of 4 | 315 | ❌ CLV fails |

**Run Line is the only market eligible for initial deployment.**

Per-half RL detail (from this session's diagnostic):

| Half | n | Win Rate | ROI | CLV |
|---|---|---|---|---|
| 2024 H1 | 83 | 56.6% | +1.20% | +1.61% |
| 2024 H2 | 55 | 60.0% | +11.83% | +1.82% |
| 2025 OOS H1 | 79 | 54.4% | +9.50% | +2.01% |
| 2025 OOS H2 | 34 | 73.5% | +33.98% | +1.35% |
| **Combined** | **251** | **59.0%** | **+10.58%** | **+1.80%** |

(2025 H2 sample size is small due to data file ending August 2025.)

---

## Audit trigger — when a deployed market gets PAUSED

A market is automatically paused for review if **ANY** of these fire on a rolling 100-pick window of live picks:

1. **Median CLV falls below -1%** — real model breakdown signal. CLV going negative means the books are systematically moving against our picks, indicating our edge has disappeared or reversed.
2. **ROI falls below -10%** — catastrophic outcome backstop. Even with positive CLV, this level of bleeding is unsustainable for product credibility and personal bankroll.
3. **BOTH ROI < 0% AND CLV < 0%** — consistent underperformance. Either alone could be variance; together is meaningful evidence the market isn't performing as expected.

**Why "rolling 100-pick window":** 100 picks is enough sample to distinguish signal from short-term variance for a market with ~+1.8% expected CLV. Smaller windows (50 picks) would fire too often on variance. Larger windows (200 picks) would delay response to genuine model breakdown.

**Why this trigger structure (rather than simple "ROI < 0%"):** ROI variance over 100 picks for a real-edge market can plausibly hit -5% just from bad luck. Pausing on -5% ROI alone could mean pausing a working model. The triple-trigger structure catches genuine problems while tolerating expected variance.

When a market is paused:

- Public picks for that market stop immediately
- Backtest is re-examined for any data drift, model decay, or methodology issue
- Decision to resume requires re-validation per these same deployment criteria
- Pause is publicly disclosed on dashboard with reason

---

## Future tightening

These criteria were calibrated for current sample sizes (~1.5 seasons of validated backtest). As data accumulates, the bar should tighten:

**At 3 full seasons of backtest data (~end of 2027 if pulling 2025 + 2026 + 2027 fresh data, or earlier if older seasons added):**
- Minimum sample raised from 250 → 500 picks
- Per-half consistency requirement: positive in 5 of 6 halves (allowing one bad half if 5 others positive)
- Currently-deployed markets must continue meeting standard or get pulled

**At 5 full seasons of backtest data:**
- Minimum sample raised to 1,000 picks
- Per-half consistency: positive in 8 of 10 halves
- Adds requirement: ROI > +1% (small positive expected long-run, not just any positive)

The escalation reflects the fact that with more data, we can demand more reliable evidence before staking reputation.

---

## Adding new markets

A market currently in development (Moneyline, Over/Under) becomes eligible if:

1. Backtest is re-run with updated model (e.g., v1.2.2)
2. Updated backtest meets all 5 deployment criteria above
3. Result is documented in a new validation summary doc
4. Operator approves before public posting

This means: when v1.2.2 (lineup-confirmed batter features) ships, the OU CLV question gets re-evaluated. If it crosses 0%, OU could deploy. Until then, OU stays in the "in development" placeholder section of the dashboard.

---

## What this doesn't cover

This doc is about **product deployment** decisions. Separate from:

- **Personal betting decisions** — operator's stake sizing on personal action is a separate question. Initial constraint: $10-25 per pick for first 100 live picks.
- **Model development criteria** — v1.2.2 validation rules will live in a separate pre-commitment doc when v1.2.2 design starts.
- **Monetization decisions** — when to start charging, pricing, packaging — separate decision after sufficient public track record.
- **Audience strategy** — content frequency, platform choices, engagement — outside scope.

---

## Things explicitly NOT permitted

- Lowering deployment criteria after seeing live results
- Cherry-picking which "halves" count after the fact
- Switching from top-1-per-day to some other selection rule mid-product without re-validation
- Adding a market to the public product on a hunch without backtest validation
- Resuming a paused market without going through the criteria again
- Publishing live record in a way that excludes losing picks

If any of these temptations arise, this doc is the lock. The discipline that produced honest v1.2.1 validation produces honest deployment decisions when applied here.

---

## Locked. The launch begins under these rules.
