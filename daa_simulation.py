#!/usr/bin/env python3
"""
Difficulty Adjustment Algorithm (DAA) Simulation
Target: 10-second block time (P2Pool share chain)
Focus: Resistance to hashrate oscillation attacks

Algorithms compared:
1. Simple Window (Bitcoin-style, adapted for per-block adjustment)
2. DigiShield v3
3. LWMA (zawy12's Linear Weighted Moving Average)
4. ASERT (aserti3-2d adapted for 10s target)
5. Dark Gravity Wave (DGW)
"""

import random
import math
import statistics
import json
from dataclasses import dataclass, field
from typing import List, Callable, Tuple

# ── Configuration ──────────────────────────────────────────────────────────
TARGET_BLOCK_TIME = 10.0  # seconds
SIMULATION_BLOCKS = 5000
NUM_RUNS = 20  # Monte Carlo runs per scenario

random.seed(42)


@dataclass
class Block:
    height: int
    timestamp: float
    difficulty: float
    hashrate: float  # hashrate active when this block was mined


@dataclass
class SimResult:
    name: str
    scenario: str
    block_times: List[float] = field(default_factory=list)
    difficulties: List[float] = field(default_factory=list)

    @property
    def mean_bt(self):
        return statistics.mean(self.block_times)

    @property
    def median_bt(self):
        return statistics.median(self.block_times)

    @property
    def stddev_bt(self):
        return statistics.stdev(self.block_times) if len(self.block_times) > 1 else 0

    @property
    def p95_bt(self):
        s = sorted(self.block_times)
        return s[int(len(s) * 0.95)]

    @property
    def p99_bt(self):
        s = sorted(self.block_times)
        return s[int(len(s) * 0.99)]

    @property
    def pct_fast(self):
        """% of blocks under 2 seconds (dangerously fast)"""
        return 100.0 * sum(1 for t in self.block_times if t < 2.0) / len(self.block_times)

    @property
    def pct_slow(self):
        """% of blocks over 30 seconds (3x target)"""
        return 100.0 * sum(1 for t in self.block_times if t > 30.0) / len(self.block_times)


# ── Mining Simulation Engine ───────────────────────────────────────────────
def mine_block(difficulty: float, hashrate: float) -> float:
    """Simulate mining time. Block time ~ Exponential(difficulty / hashrate)."""
    expected_time = difficulty / hashrate
    return random.expovariate(1.0 / expected_time)


# ── Hashrate Scenarios ─────────────────────────────────────────────────────
def steady_hashrate(block_height: int, total_blocks: int) -> float:
    """Constant hashrate baseline."""
    return 1.0


def gradual_growth(block_height: int, total_blocks: int) -> float:
    """Hashrate grows 10x over the simulation."""
    return 1.0 + 9.0 * (block_height / total_blocks)


def oscillation_attack(block_height: int, total_blocks: int) -> float:
    """
    Hashrate oscillation attack: attacker with 9x the base hashrate
    mines for ~50 blocks then leaves for ~50 blocks, cycling.
    This simulates a large miner hopping on/off the chain.
    """
    cycle = block_height % 100
    if cycle < 50:
        return 10.0  # attacker present: 1 (base) + 9 (attacker)
    else:
        return 1.0   # attacker gone: just base miners


def sudden_drop(block_height: int, total_blocks: int) -> float:
    """90% hashrate drop at block 1000, then stays low."""
    if block_height < 1000:
        return 10.0
    return 1.0


def noisy_hashrate(block_height: int, total_blocks: int) -> float:
    """Random fluctuations: uniform between 0.5x and 2x."""
    return 0.5 + 1.5 * random.random()


def rapid_oscillation(block_height: int, total_blocks: int) -> float:
    """
    Faster oscillation attack: 20-block cycles.
    More aggressive attacker pattern for a 10s target chain.
    """
    cycle = block_height % 20
    if cycle < 10:
        return 10.0
    else:
        return 1.0


SCENARIOS = {
    "Steady State": steady_hashrate,
    "Gradual 10x Growth": gradual_growth,
    "Oscillation Attack (100-blk cycle)": oscillation_attack,
    "Rapid Oscillation (20-blk cycle)": rapid_oscillation,
    "Sudden 90% Drop": sudden_drop,
    "Noisy Random": noisy_hashrate,
}


# ── Difficulty Adjustment Algorithms ───────────────────────────────────────

def clamp(value, lo, hi):
    return max(lo, min(hi, value))


# 1. Simple Moving Average (window-based, Bitcoin-inspired but per-block)
def daa_sma(chain: List[Block], target: float) -> float:
    """Simple moving average over last N blocks."""
    N = 72  # ~12 minutes of blocks at target
    if len(chain) < N + 1:
        return chain[-1].difficulty

    window = chain[-(N + 1):]
    actual_time = window[-1].timestamp - window[0].timestamp
    expected_time = N * target

    if actual_time <= 0:
        actual_time = 1.0

    ratio = expected_time / actual_time
    ratio = clamp(ratio, 0.25, 4.0)

    return chain[-1].difficulty * ratio


# 2. DigiShield v3
def daa_digishield(chain: List[Block], target: float) -> float:
    """DigiShield v3 with dampening factor."""
    N = 17  # window
    if len(chain) < N + 1:
        return chain[-1].difficulty

    window = chain[-(N + 1):]
    actual_time = window[-1].timestamp - window[0].timestamp
    expected_time = N * target

    if actual_time <= 0:
        actual_time = 1.0

    # DigiShield dampening: dampen the deviation by factor of 4
    actual_time = expected_time + (actual_time - expected_time) / 4.0

    # Clamp to prevent extreme adjustments
    if actual_time < expected_time * 0.75:
        actual_time = expected_time * 0.75
    if actual_time > expected_time * 1.5:
        actual_time = expected_time * 1.5

    return chain[-1].difficulty * (expected_time / actual_time)


# 3. LWMA (zawy12)
def daa_lwma(chain: List[Block], target: float) -> float:
    """
    Linear Weighted Moving Average - zawy12's algorithm.
    More responsive than DigiShield, weights recent blocks heavily.
    """
    N = 45  # window (zawy recommends N=45 for small chains)
    if len(chain) < N + 1:
        return chain[-1].difficulty

    window = chain[-(N + 1):]

    weighted_sum = 0.0
    weight_total = 0
    for i in range(1, N + 1):
        solve_time = window[i].timestamp - window[i - 1].timestamp
        # Clamp individual solve times to prevent timestamp manipulation
        solve_time = clamp(solve_time, -6 * target, 6 * target)
        weighted_sum += solve_time * i
        weight_total += i

    # Average weighted solve time
    avg_weighted = weighted_sum / weight_total

    if avg_weighted <= 0:
        avg_weighted = target * 0.1

    # Difficulty of the tip
    # Use average difficulty over the window
    sum_diff = sum(window[i].difficulty for i in range(1, N + 1))
    avg_diff = sum_diff / N

    new_diff = avg_diff * target / avg_weighted

    # Limit adjustment per block
    prev_diff = chain[-1].difficulty
    max_change = 1.5
    new_diff = clamp(new_diff, prev_diff / max_change, prev_diff * max_change)

    return max(new_diff, 0.001)


# 4. ASERT (Absolutely Scheduled Exponentially Rising Targets)
# Adapted for 10-second target with half-life tuned for fast chains
class ASERTState:
    def __init__(self, target_time: float):
        self.anchor_height = None
        self.anchor_time = None
        self.anchor_difficulty = None
        self.target_time = target_time
        # Half-life: how many seconds of deviation cause difficulty to halve/double
        # For 10s target, ~600s (1 minute of blocks = ~6 blocks) is responsive
        # zawy recommends half_life = 2 * N * target where N ~ 30
        self.half_life = 2 * 30 * target_time  # 600 seconds

    def reset(self):
        self.anchor_height = None
        self.anchor_time = None
        self.anchor_difficulty = None


ASERT_STATE = ASERTState(TARGET_BLOCK_TIME)


def daa_asert(chain: List[Block], target: float) -> float:
    """
    ASERT: difficulty is a pure function of anchor block + current state.
    Immune to block ordering attacks.
    """
    state = ASERT_STATE

    if state.anchor_height is None:
        # Set anchor at first block
        state.anchor_height = chain[0].height
        state.anchor_time = chain[0].timestamp
        state.anchor_difficulty = chain[0].difficulty

    current = chain[-1]

    # Time since anchor
    time_delta = current.timestamp - state.anchor_time
    # Expected time since anchor
    height_delta = current.height - state.anchor_height
    expected_time = height_delta * target

    # Exponent: positive means blocks are too slow, negative means too fast
    exponent = (time_delta - expected_time) / state.half_life

    # Clamp exponent to prevent overflow
    exponent = clamp(exponent, -20, 20)

    # New difficulty = anchor_difficulty * 2^(-exponent)
    # If blocks are slow (time_delta > expected), exponent > 0, difficulty decreases
    # If blocks are fast (time_delta < expected), exponent < 0, difficulty increases
    new_diff = state.anchor_difficulty * math.pow(2, -exponent)

    return max(new_diff, 0.001)


# 5. Dark Gravity Wave (DGW v3)
def daa_dgw(chain: List[Block], target: float) -> float:
    """
    Dark Gravity Wave v3 - multiple EMA passes.
    """
    N = 24  # window
    if len(chain) < N + 1:
        return chain[-1].difficulty

    window = chain[-(N + 1):]

    actual_time = window[-1].timestamp - window[0].timestamp
    expected_time = N * target

    if actual_time <= 0:
        actual_time = 1.0

    # Average difficulty over the window
    sum_diff = sum(window[i].difficulty for i in range(1, N + 1))
    avg_diff = sum_diff / N

    ratio = expected_time / actual_time
    ratio = clamp(ratio, 1.0 / 3.0, 3.0)

    return avg_diff * ratio


# 6. LWMA with tighter window (more aggressive for 10s target)
def daa_lwma_tight(chain: List[Block], target: float) -> float:
    """
    LWMA with N=20, more aggressive for very fast block times.
    """
    N = 20
    if len(chain) < N + 1:
        return chain[-1].difficulty

    window = chain[-(N + 1):]

    weighted_sum = 0.0
    weight_total = 0
    for i in range(1, N + 1):
        solve_time = window[i].timestamp - window[i - 1].timestamp
        solve_time = clamp(solve_time, -6 * target, 6 * target)
        weighted_sum += solve_time * i
        weight_total += i

    avg_weighted = weighted_sum / weight_total
    if avg_weighted <= 0:
        avg_weighted = target * 0.1

    sum_diff = sum(window[i].difficulty for i in range(1, N + 1))
    avg_diff = sum_diff / N

    new_diff = avg_diff * target / avg_weighted

    prev_diff = chain[-1].difficulty
    new_diff = clamp(new_diff, prev_diff / 2.0, prev_diff * 2.0)

    return max(new_diff, 0.001)


ALGORITHMS = {
    "SMA-72": daa_sma,
    "DigiShield": daa_digishield,
    "LWMA-45": daa_lwma,
    "LWMA-20 (tight)": daa_lwma_tight,
    "ASERT": daa_asert,
    "DGW v3": daa_dgw,
}


# ── Simulation Runner ──────────────────────────────────────────────────────

def run_simulation(
    daa_fn: Callable,
    hashrate_fn: Callable,
    num_blocks: int,
    target: float,
    daa_name: str,
) -> SimResult:
    """Run a single simulation."""
    # Genesis block
    genesis = Block(height=0, timestamp=0.0, difficulty=target, hashrate=1.0)
    chain = [genesis]

    result = SimResult(name=daa_name, scenario="")

    for h in range(1, num_blocks + 1):
        hr = hashrate_fn(h, num_blocks)
        diff = daa_fn(chain, target)
        solve_time = mine_block(diff, hr)

        block = Block(
            height=h,
            timestamp=chain[-1].timestamp + solve_time,
            difficulty=diff,
            hashrate=hr,
        )
        chain.append(block)
        result.block_times.append(solve_time)
        result.difficulties.append(diff)

    return result


def run_monte_carlo(
    daa_name: str,
    daa_fn: Callable,
    scenario_name: str,
    hashrate_fn: Callable,
    num_blocks: int,
    target: float,
    num_runs: int,
) -> dict:
    """Run multiple simulations and aggregate results."""
    all_bt = []
    all_means = []
    all_stddevs = []
    all_p95 = []
    all_p99 = []
    all_pct_fast = []
    all_pct_slow = []

    for run in range(num_runs):
        random.seed(42 + run * 1000)
        # Reset ASERT anchor for each run
        if daa_name == "ASERT":
            ASERT_STATE.reset()

        res = run_simulation(daa_fn, hashrate_fn, num_blocks, target, daa_name)
        # Skip warmup period (first 100 blocks)
        bt = res.block_times[100:]
        all_bt.extend(bt)
        all_means.append(statistics.mean(bt))
        all_stddevs.append(statistics.stdev(bt))
        s = sorted(bt)
        all_p95.append(s[int(len(s) * 0.95)])
        all_p99.append(s[int(len(s) * 0.99)])
        all_pct_fast.append(100.0 * sum(1 for t in bt if t < 2.0) / len(bt))
        all_pct_slow.append(100.0 * sum(1 for t in bt if t > 30.0) / len(bt))

    return {
        "algorithm": daa_name,
        "scenario": scenario_name,
        "mean_bt": statistics.mean(all_means),
        "median_bt": statistics.median(all_bt),
        "stddev_bt": statistics.mean(all_stddevs),
        "p95_bt": statistics.mean(all_p95),
        "p99_bt": statistics.mean(all_p99),
        "pct_fast_lt2s": statistics.mean(all_pct_fast),
        "pct_slow_gt30s": statistics.mean(all_pct_slow),
        # Attack resistance score: lower is better
        # Composite of deviation from target + tail behavior
        "deviation_score": abs(statistics.mean(all_means) - target) / target * 100,
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 90)
    print("DIFFICULTY ADJUSTMENT ALGORITHM SIMULATION")
    print(f"Target block time: {TARGET_BLOCK_TIME}s | Blocks per run: {SIMULATION_BLOCKS} | Monte Carlo runs: {NUM_RUNS}")
    print("=" * 90)

    all_results = []

    for scenario_name, hashrate_fn in SCENARIOS.items():
        print(f"\n{'─' * 90}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'─' * 90}")
        print(f"{'Algorithm':<18} {'Mean':>7} {'Median':>7} {'StdDev':>7} "
              f"{'P95':>7} {'P99':>7} {'<2s%':>6} {'>30s%':>6} {'Dev%':>6}")
        print(f"{'─' * 18} {'─' * 7} {'─' * 7} {'─' * 7} "
              f"{'─' * 7} {'─' * 7} {'─' * 6} {'─' * 6} {'─' * 6}")

        scenario_results = []
        for algo_name, algo_fn in ALGORITHMS.items():
            result = run_monte_carlo(
                algo_name, algo_fn, scenario_name, hashrate_fn,
                SIMULATION_BLOCKS, TARGET_BLOCK_TIME, NUM_RUNS
            )
            scenario_results.append(result)
            all_results.append(result)

            print(f"{result['algorithm']:<18} "
                  f"{result['mean_bt']:>7.2f} "
                  f"{result['median_bt']:>7.2f} "
                  f"{result['stddev_bt']:>7.2f} "
                  f"{result['p95_bt']:>7.2f} "
                  f"{result['p99_bt']:>7.2f} "
                  f"{result['pct_fast_lt2s']:>6.1f} "
                  f"{result['pct_slow_gt30s']:>6.1f} "
                  f"{result['deviation_score']:>6.1f}")

    # ── Overall Rankings ───────────────────────────────────────────────────
    print(f"\n{'=' * 90}")
    print("OVERALL RANKING (lower composite score = better)")
    print("Composite = mean_deviation% + stddev_weight + tail_penalty")
    print(f"{'=' * 90}")

    # Compute composite score per algorithm across all scenarios
    algo_scores = {}
    for algo_name in ALGORITHMS:
        algo_results = [r for r in all_results if r["algorithm"] == algo_name]
        # Weighted composite:
        # - deviation from target (want mean close to 10s)
        # - stddev (want low variance)
        # - tail behavior (penalize slow blocks heavily, they stall the chain)
        # - attack scenarios weighted 2x
        total_score = 0
        for r in algo_results:
            is_attack = "Oscillation" in r["scenario"] or "Drop" in r["scenario"]
            weight = 2.0 if is_attack else 1.0

            deviation_penalty = abs(r["mean_bt"] - TARGET_BLOCK_TIME) / TARGET_BLOCK_TIME * 100
            variance_penalty = r["stddev_bt"] / TARGET_BLOCK_TIME * 10
            tail_penalty = r["pct_slow_gt30s"] * 5  # heavy penalty for stalled blocks
            fast_penalty = r["pct_fast_lt2s"] * 2    # penalty for too-fast blocks

            total_score += weight * (deviation_penalty + variance_penalty + tail_penalty + fast_penalty)

        algo_scores[algo_name] = total_score

    ranked = sorted(algo_scores.items(), key=lambda x: x[1])
    for rank, (name, score) in enumerate(ranked, 1):
        marker = " ★ RECOMMENDED" if rank == 1 else ""
        print(f"  {rank}. {name:<18} score: {score:>8.1f}{marker}")

    # ── Attack-specific ranking ────────────────────────────────────────────
    print(f"\n{'=' * 90}")
    print("ATTACK RESISTANCE RANKING (oscillation + sudden drop scenarios only)")
    print(f"{'=' * 90}")

    attack_scenarios = [s for s in SCENARIOS if "Oscillation" in s or "Drop" in s]
    algo_attack_scores = {}
    for algo_name in ALGORITHMS:
        attack_results = [r for r in all_results
                         if r["algorithm"] == algo_name and r["scenario"] in attack_scenarios]
        score = 0
        for r in attack_results:
            score += abs(r["mean_bt"] - TARGET_BLOCK_TIME) / TARGET_BLOCK_TIME * 100
            score += r["pct_slow_gt30s"] * 10
            score += r["stddev_bt"] / TARGET_BLOCK_TIME * 20
        algo_attack_scores[algo_name] = score

    ranked_attack = sorted(algo_attack_scores.items(), key=lambda x: x[1])
    for rank, (name, score) in enumerate(ranked_attack, 1):
        marker = " ★ BEST ATTACK RESISTANCE" if rank == 1 else ""
        print(f"  {rank}. {name:<18} attack score: {score:>8.1f}{marker}")

    # Save JSON for charting
    with open("/home/claude/daa_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDetailed results saved to daa_results.json")


if __name__ == "__main__":
    main()
