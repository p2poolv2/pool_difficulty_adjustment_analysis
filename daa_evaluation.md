# Difficulty Adjustment Algorithm Evaluation for P2Pool v2

## Parameters

- Target block time: 10 seconds
- Uncle blocks: max 3 per share, max depth 3
- Uncle PPLNS: discounted, referrer bonus
- Simulation: 5,000 blocks × 20 Monte Carlo runs per scenario
- Metrics: mean block time, standard deviation, P95, P99, % blocks < 2s, % blocks > 30s, deviation from target

## Scenarios

| Scenario | Description |
|---|---|
| Steady State | Constant hashrate |
| Gradual 10x Growth | Hashrate grows 10x over simulation |
| Oscillation Attack (100-blk) | 9x attacker cycles on/off every 50 blocks |
| Rapid Oscillation (20-blk) | 9x attacker cycles on/off every 10 blocks |
| Sudden 90% Drop | Hashrate drops from 10x to 1x at block 1000 |
| Noisy Random | Uniform random hashrate between 0.5x and 2x |

## Algorithms Evaluated

| Algorithm | Window | Key Mechanism |
|---|---|---|
| SMA-72 | 72 blocks | Simple moving average |
| DigiShield v3 | 17 blocks | Dampened SMA (4x dampening factor) |
| LWMA-45 | 45 blocks | Linear weighted moving average (zawy12) |
| LWMA-20 | 20 blocks | LWMA with tighter window |
| ASERT | Anchor-based | Exponential, pure function of anchor + current state |
| DGW v3 | 24 blocks | Multiple EMA (Dark Gravity Wave) |

## Results

### Overall Ranking (lower = better)

| Rank | Algorithm | Composite Score |
|---|---|---|
| 1 | ASERT | 939.4 |
| 2 | DGW v3 | 1,059.7 |
| 3 | LWMA-20 | 1,124.4 |
| 4 | LWMA-45 | 1,125.7 |
| 5 | DigiShield | 1,280.7 |
| 6 | SMA-72 | 5,230.6 |

### Attack Resistance Ranking (oscillation + sudden drop only)

| Rank | Algorithm | Attack Score |
|---|---|---|
| 1 | ASERT | 328.1 |
| 2 | DigiShield | 432.8 |
| 3 | DGW v3 | 441.9 |
| 4 | LWMA-45 | 491.7 |
| 5 | LWMA-20 | 491.9 |
| 6 | SMA-72 | 2,130.3 |

### Per-Scenario Detail (excluding SMA-72)

#### Steady State

| Algorithm | Mean | StdDev | P95 | P99 | >30s% | Dev% |
|---|---|---|---|---|---|---|
| ASERT | 10.00 | 10.03 | 29.92 | 46.53 | 4.9 | 0.0 |
| LWMA-45 | 10.17 | 10.38 | 30.73 | 47.91 | 5.4 | 1.7 |
| DGW v3 | 10.23 | 10.66 | 31.19 | 49.57 | 5.6 | 2.3 |
| DigiShield | 10.28 | 14.02 | 36.45 | 66.47 | 7.4 | 2.8 |

#### Oscillation Attack (100-block cycle)

| Algorithm | Mean | StdDev | P95 | P99 | >30s% | Dev% |
|---|---|---|---|---|---|---|
| ASERT | 9.97 | 15.49 | 41.65 | 73.61 | 9.3 | 0.3 |
| DigiShield | 10.83 | 21.67 | 44.20 | 99.26 | 9.1 | 8.3 |
| DGW v3 | 14.49 | 27.78 | 53.79 | 133.93 | 11.7 | 44.9 |
| LWMA-45 | 15.49 | 26.29 | 62.15 | 125.81 | 14.9 | 54.9 |

#### Rapid Oscillation (20-block cycle)

| Algorithm | Mean | StdDev | P95 | P99 | >30s% | Dev% |
|---|---|---|---|---|---|---|
| ASERT | 9.96 | 15.28 | 41.42 | 71.64 | 9.5 | 0.4 |
| DGW v3 | 10.64 | 17.18 | 44.31 | 81.17 | 10.0 | 6.4 |
| LWMA-45 | 10.84 | 17.10 | 45.53 | 80.01 | 10.8 | 8.4 |
| DigiShield | 11.43 | 30.11 | 60.05 | 146.98 | 10.6 | 14.3 |

#### Sudden 90% Drop

| Algorithm | Mean | StdDev | P95 | P99 | >30s% | Dev% |
|---|---|---|---|---|---|---|
| ASERT | 10.17 | 11.52 | 30.69 | 49.51 | 5.3 | 1.7 |
| DGW v3 | 10.35 | 11.45 | 31.50 | 50.68 | 5.7 | 3.5 |
| LWMA-45 | 10.42 | 11.55 | 31.54 | 50.53 | 5.7 | 4.2 |
| DigiShield | 10.35 | 15.10 | 36.61 | 67.43 | 7.5 | 3.5 |

## Uncle Blocks and Difficulty

SChernykh's Monero p2pool uses a trimmed-mean window algorithm that includes uncle block data in the difficulty calculation window. We evaluated two approaches for ASERT:

1. **Main-chain only ASERT** — ignores uncles in DAA, uses static correction for expected uncle rate
2. **Topo-ASERT** — uses `effective_height = main_height + cumulative_uncle_count`, counting total share events

With max 3 uncles per share, depth limit 3, and PPLNS discount on uncles, the uncle spam attack surface is bounded and economically disincentivized.

## Integer vs Floating-Point Arithmetic

| Implementation | Relative Error | nBits Mismatches per 100k Blocks |
|---|---|---|
| Integer fixed-point (16-bit radix) | 0 | 0 |
| f64 naive | ~1e-4 | 99,490 |
| f64 careful (float for 2^frac only) | ~1e-4 | 99,490 |

f64 targets lose up to 158 bits of precision when converting 211-bit targets. Integer arithmetic is required for consensus.

## Decision

ASERT with integer fixed-point arithmetic.

### Parameters

| Parameter | Value |
|---|---|
| Target block time | 10 seconds |
| Half-life | 600 seconds |
| Anchor | Share chain genesis |
| Height counter | `effective_height = main_height + cumulative_uncle_count` |
| Arithmetic | Integer, 16-bit fixed-point radix |
| Taylor polynomial | Degree 3 (coefficients from BCH aserti3-2d) |
