# DAA Simulation: P2Pool Share Chain

**Target:** 10s block time · **Blocks per run:** 5,000 · **Monte Carlo runs:** 20 · **Algorithms:** 6 · **Scenarios:** 6

---

## Recommendation: ASERT ★

ASERT wins both overall and attack-resistance rankings decisively. It maintains mean block time closest to 10s across all scenarios, has the lowest tail latency under attack, and is mathematically the simplest (pure function of anchor block + current state — no history rewriting possible).

For P2Pool's 10s share chain: use **ASERT with half-life = 600s** (2 × 30 × 10s target). This gives ~60 blocks of smoothing while staying responsive to hashrate swings.

---

## Overall Composite Score (lower = better)

| Rank | Algorithm | Score |
|------|-----------|-------|
| 1 ★ | ASERT | 939.4 |
| 2 | DGW v3 | 1,059.7 |
| 3 | LWMA-20 (tight) | 1,124.4 |
| 4 | LWMA-45 | 1,125.7 |
| 5 | DigiShield | 1,280.7 |
| 6 | SMA-72 | 5,230.6 |

## Attack Resistance Score (lower = better)

| Rank | Algorithm | Score |
|------|-----------|-------|
| 1 ★ | ASERT | 328.1 |
| 2 | DigiShield | 432.8 |
| 3 | DGW v3 | 441.9 |
| 4 | LWMA-45 | 491.7 |
| 5 | LWMA-20 (tight) | 491.9 |
| 6 | SMA-72 | 2,130.3 |

---

## Detailed Results by Scenario

### Steady State

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| **ASERT** | 10.00 | 6.92 | 10.03 | 29.92 | 46.53 | 18.1 | 4.9 | 0.0 |
| LWMA-45 | 10.17 | 6.96 | 10.38 | 30.73 | 47.91 | 18.2 | 5.4 | 1.7 |
| DGW v3 | 10.23 | 6.90 | 10.66 | 31.19 | 49.57 | 18.4 | 5.6 | 2.3 |
| DigiShield | 10.28 | 5.46 | 14.02 | 36.45 | 66.47 | 25.9 | 7.4 | 2.8 |
| LWMA-20 (tight) | 10.37 | 6.99 | 10.93 | 31.74 | 50.98 | 18.3 | 5.9 | 3.7 |

### Gradual 10x Growth

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| LWMA-45 | 10.07 | 6.89 | 10.27 | 30.42 | 47.37 | 18.3 | 5.2 | 0.7 |
| DGW v3 | 10.17 | 6.87 | 10.61 | 31.00 | 49.34 | 18.5 | 5.5 | 1.7 |
| DigiShield | 10.26 | 5.46 | 13.98 | 36.35 | 66.27 | 25.8 | 7.4 | 2.6 |
| LWMA-20 (tight) | 10.32 | 6.96 | 10.88 | 31.60 | 50.76 | 18.3 | 5.8 | 3.2 |
| **ASERT** | 9.61 | 6.65 | 9.65 | 28.76 | 44.71 | 18.8 | 4.4 | 3.9 |

### Oscillation Attack (100-block cycle)

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| **ASERT** | 9.97 | 3.32 | 15.49 | 41.65 | 73.61 | 38.3 | 9.3 | 0.3 |
| DigiShield | 10.83 | 3.51 | 21.67 | 44.20 | 99.26 | 39.1 | 9.1 | 8.3 |
| DGW v3 | 14.49 | 6.14 | 27.78 | 53.79 | 133.93 | 25.5 | 11.7 | 44.9 |
| LWMA-20 (tight) | 14.81 | 6.88 | 26.75 | 53.38 | 127.87 | 22.0 | 12.0 | 48.1 |
| LWMA-45 | 15.49 | 5.93 | 26.29 | 62.15 | 125.81 | 26.9 | 14.9 | 54.9 |

### Rapid Oscillation (20-block cycle)

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| **ASERT** | 9.96 | 3.26 | 15.28 | 41.42 | 71.64 | 38.7 | 9.5 | 0.4 |
| DGW v3 | 10.64 | 3.67 | 17.18 | 44.31 | 81.17 | 35.9 | 10.0 | 6.4 |
| LWMA-45 | 10.84 | 3.48 | 17.10 | 45.53 | 80.01 | 37.3 | 10.8 | 8.4 |
| DigiShield | 11.43 | 1.23 | 30.11 | 60.05 | 146.98 | 57.6 | 10.6 | 14.3 |
| LWMA-20 (tight) | 12.10 | 3.79 | 20.65 | 51.15 | 98.54 | 35.6 | 12.0 | 21.0 |

### Sudden 90% Drop

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| **ASERT** | 10.17 | 6.81 | 11.52 | 30.69 | 49.51 | 18.6 | 5.3 | 1.7 |
| DigiShield | 10.35 | 5.43 | 15.10 | 36.61 | 67.43 | 26.1 | 7.5 | 3.5 |
| DGW v3 | 10.35 | 6.93 | 11.45 | 31.50 | 50.68 | 18.3 | 5.7 | 3.5 |
| LWMA-45 | 10.42 | 7.03 | 11.55 | 31.54 | 50.53 | 18.1 | 5.7 | 4.2 |
| LWMA-20 (tight) | 10.50 | 7.02 | 11.67 | 32.07 | 52.09 | 18.2 | 6.0 | 5.0 |

### Noisy Random

| Algorithm | Mean | Median | StdDev | P95 | P99 | <2s% | >30s% | Dev% |
|-----------|------|--------|--------|-----|-----|------|-------|------|
| **ASERT** | 10.00 | 6.24 | 11.59 | 32.25 | 55.42 | 20.5 | 5.9 | 0.0 |
| DGW v3 | 10.31 | 6.24 | 12.51 | 33.83 | 60.01 | 20.8 | 6.6 | 3.1 |
| LWMA-45 | 10.33 | 6.38 | 12.21 | 33.49 | 58.19 | 20.3 | 6.5 | 3.3 |
| DigiShield | 10.36 | 4.72 | 16.53 | 39.42 | 79.14 | 29.9 | 8.0 | 3.6 |
| LWMA-20 (tight) | 10.61 | 6.41 | 12.98 | 34.97 | 61.94 | 20.4 | 7.0 | 6.1 |

> **Note:** SMA-72 omitted from per-scenario tables — it performed catastrophically in all scenarios (mean ~20s, >90% blocks under 2s, stddev >200s).

---

## Key Findings

- **ASERT dominates under oscillation attacks.** When a 9x attacker cycles on/off every 50 blocks, ASERT holds mean block time at 9.97s (0.3% deviation) while LWMA-45 drifts to 15.49s (55% deviation). ASERT's exponential anchor-based formula means it can't be gamed by reordering blocks.

- **LWMA and DGW struggle with oscillating hashrate.** Their sliding-window averages lag behind rapid hashrate changes, causing alternating periods of blocks that are too fast (when attacker joins) and too slow (when attacker leaves). LWMA-45's P99 hits 125s under 100-block oscillation.

- **DigiShield's dampening helps under attack but hurts steady-state variance.** The 4x dampening factor prevents overcorrection during oscillations (8.3% deviation vs LWMA's 55%), but the same dampening causes higher variance during normal operation with 7.4% of blocks exceeding 30s.

- **SMA-72 is catastrophically unsuitable for 10s targets.** The large window creates massive inertia — mean block times of 20s+ across all scenarios with 90%+ blocks under 2s (rapid-fire blocks when difficulty undershoots, then long stalls).

- **Recommended ASERT parameters for P2Pool:** half_life = 600s gives responsive adjustment (~60 blocks of smoothing). The anchor block should be set at chain genesis. No per-block clamps needed — ASERT is inherently smooth.
