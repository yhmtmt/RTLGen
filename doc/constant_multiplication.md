# Multiplierless Multiple Constant Multiplication (Voronenko & Püschel, 2007)

## Overview
- Tackles the multiple constant multiplication (MCM) problem: implementing products `t_i · x` using only additions/subtractions and shifts to avoid costly multipliers in DSP hardware/software.
- Introduces a unifying framework for graph-based MCM synthesis built around *A-operations* (single add/subtract plus configurable shifts) and the notion of *A-distance* between a ready set `R` of synthesized fundamentals and remaining targets `T`.
- Presents a new heuristic algorithm that reduces add/subtract counts by up to 20% compared to the then state-of-the-art RAG-n approach and, unlike RAG-n, scales beyond 19-bit constants because it avoids exhaustive SCM lookup tables.

## Formal Framework
- Defines A-operations with bounded shifts (≤ `b+1` for `b`-bit targets) and restricts all fundamentals to odd values by preprocessing targets with right shifts.
- General graph-based synthesis iteratively grows a ready set `R` from `{1}`, choosing successors `s` from `S = A*(R,R)` (distance-1 candidates) until `T ⊆ R`.
- Demonstrates how classic algorithms (BHA, BHM, RAG-n) fit this template through their successor selection heuristics and constraints.

## New Algorithm
- Keeps the optimal RAG-n behavior for distance-1 targets by incrementally maintaining `S` through a worklist, synthesizing any `t ∈ S ∩ T` immediately (provably optimal when all targets are caught here).
- When no distance-1 targets remain, invokes a heuristic that adds exactly one intermediate successor at a time, enabling finer-grained control than RAG-n’s bulk additions.
- Two admissible heuristics score each `s ∈ S` via weighted benefits `B(R,s,t) = 10^{-dist(R+s,t)}(dist(R,t)-dist(R+s,t))`:
  - `H_maxb` maximizes the best individual benefit across targets (∞-norm behavior).
  - `H_cub` sums weighted benefits across all targets (≈1-norm), giving superior joint optimization; this is the recommended variant.
- Termination follows from using an admissible distance estimator that guarantees some successor always decreases the summed distance metric.

## Computing / Estimating A-Distance
- Proves exact A-distance computation (with bounded shifts) is NP-complete, motivating selective exact tests plus estimation.
- Supplies exact feasibility tests for distances 1–3 by enumerating small A-graph topologies and solving corresponding A-equations (set intersections such as `A*(R,t) ∩ S`).
- For larger distances, derives overestimates from partial topologies (Fig. 10), isolating an unknown subproblem `z` whose cost is approximated via CSD weight: `dist(R+s,t) ≲ Est(Z)+#ops−1`.
- Shows the estimator remains admissible (benefits never negative) and caches `dist(R,t)` updates to control runtime.

## Complexity & Runtime
- Provides worst-case set sizes: `|R| = O(nb)`, `|S| = O(n² b³)`, `|C1| = O(b)`, `|C2| = O(b²)` for bitwidth `b` and `n = |T|`.
- With exact distance-3 tests the heuristic loop costs `O(n³ b⁵ log(nb))`; dropping to distance-2 tests only reduces complexity to `O(n³ b⁵)` with ≤3–5% solution degradation for moderate `b`.
- Offers the first detailed runtime analyses for BHM and RAG-n, showing RAG-n is dominated by successor-set construction `O(n² b³ log(nb))` while BHM grows as `O(n³ b⁴)`.

## Experimental Highlights
- Benchmarks on 100–200 random target sets show `H_cub` consistently achieves the lowest operation counts across `b ≤ 32` and `n ≤ 100`.
- Improvements over RAG-n peak around 20% fewer adds/subtracts for 16–19 bit, 20–80 constant workloads; gains stay ≥10% for many larger-bitwidth cases where RAG-n is unusable.
- Distance-3 tests matter most for small `n` or very large `b`; for large `n` their benefit diminishes, validating the option to omit them when runtime dominates.
- Runtime measurements on a 3.4 GHz Pentium 4 show single-digit seconds for typical FIR-sized problems (e.g., `n=20`, `b=22` completes in ≈4 s; `n=100`, `b=32` needs ≈2.3 h but remains feasible for offline design).

## Takeaways
- The paper elevates MCM synthesis by unifying prior heuristics, formalizing a reusable distance-based framework, and delivering a practical algorithm that trades compute time for materially smaller adder/subtractor counts without bitwidth limits.
- Exact distance tests plus CSD-driven estimates ensure admissibility and guide heuristic selection, while benefit aggregation (`H_cub`) captures cross-target sharing opportunities absent in earlier methods.
- Future work suggested by the authors includes reusing the framework to co-optimize for delay/register pressure and tightening asymptotic bounds on SCM/MCM costs.

## Reference Implementation

The `src/` directory now contains a small C++17 driver (`mcm_cli`) that exercises four algorithms in increasing order of sophistication:

1. **BHA** – Bull & Horrocks' original add/subtract/shift graph builder.
2. **BHM** – Dempster & Macleod's Aodd variant with complexity-aware ordering.
3. **RAG-n** – Reduced Adder Graph with distance-1/2 tests and a CSD-based fallback for single constants.
4. **H_cub** – The paper's cumulative-benefit heuristic, using lightweight A-distance estimates and benefit aggregation to pick intermediates.

All algorithms share common A-operation primitives and operate on odd fundamentals (targets are right-shifted until odd when required). The implementations favor clarity over absolute optimality but follow the decision logic outlined in the paper, including heuristic distance ranking, successor generation, and staged synthesis.

### CSE-Based Optimization (Aksoy et al., 2012)
- Focuses on constant matrix–vector multiplication (CMVM) and frames common subexpression elimination as an exact 0–1 ILP problem by wiring the data-flow graph into a Boolean network whose gates translate to pseudo-Boolean constraints; SAT/ILP solvers can deliver optimal add/subtract counts for up to roughly 12-term expressions (Table II), giving ground-truth optima for small transforms.
- Introduces **H2MC**, a scalable heuristic that repeatedly extracts the most frequent, least-conflicting 2-term subexpression (allowing signed digits and shifts), substitutes it back into every remaining row, and iterates—capturing much richer sharing than column-wise CSD scans while retaining CSE-like runtime.
- Proposes **H_CMVM**, a hybrid that first applies a numerical-difference method to linearly combine rows into a friendlier basis (difference rows often have sparser CSD forms), then runs H2MC; the staged approach mitigates the representation dependence that usually limits CSE algorithms.
- Experimental sweep on random k×2 matrices with 6-bit constants shows H_CMVM cuts add/subtract counts by ~10–15% versus the Hosangadi et al. CSE heuristic (e.g., 36.7 vs 41.7 adds for 20×2 matrices) and tracks the exact ILP optimum whenever solvable; synthesized 8- and 16-point DCT blocks see proportional gate-count reductions when using the heuristic-derived shift-add networks.
- Added `cmvm_cli` (backed by Google OR-Tools) implementing the **Exact ILP**, **H2MC**, and **H_CMVM** algorithms.  It reads a dense matrix in row-major order and reports baseline and optimized operation counts.  Example:
  ```bash
  cd mcm
  cmake -S . -B build
  cmake --build build
  ./build/cmvm_cli 2 2 6 5 7 1 3
  ```
  which corresponds to the transform `[5 7; 1 3]`.  The build automatically links against the isolated OR-Tools bundle in `~/work/or-tools_x86_64_Ubuntu-24.04_cpp_v9.10.4067`, so no system-level packages are needed.  The resulting executable carries an rpath to that bundle, but if you relocate it, export `LD_LIBRARY_PATH` accordingly.

### ILP-Based MCM (Garcia & Volkova, 2023)
- Implements the *Toward the Multiple Constant Multiplication at Minimal Hardware Cost* MILP model that encodes fundamentals, shifts, and signed selections directly as integer/binary decision variables. The solver enforces odd fundamentals, optional right shifts and target coverage while minimizing the number of adders within a fixed budget.
- The command-line tool `mcm_ilp_cli` wires the ILP core to OR-Tools’ CBC backend. It expects a bit-width, the target constants, and either an explicit adder budget (`--adder-count <N>`) or an estimator name (`--estimator BHA|BHM|RAGn|H_cub`). Estimators reuse the existing heuristic implementations to deliver the initial budget Garcia & Volkova require before solving.
- Output mirrors the legacy CLI: synthesized targets, total add/sub operations used inside the budget, plus the exact sequence of operations (using `Operation::describe`) so the ILP graph can be replayed or verified.
- Example:
  ```bash
  ./build/mcm_ilp_cli 10 127 255 341 --estimator hcub
  # or pin the budget
  ./build/mcm_ilp_cli 10 127 255 341 --adder-count 8
  ```
- The Google Test suite now exercises both a fixed-budget and estimator-driven solve to guard the integration.

### Build
```bash
cd mcm
cmake -S . -B build
cmake --build build
```

### Run
```bash
./build/mcm_cli <bitwidth> <target1> [target2 ...]
# Example:
./build/mcm_cli 8 23 81
```

The CLI prints the number of synthesized add/subtract nodes and the order in which each algorithm reaches the requested constants.

### Test
```bash
cd mcm/build
ctest --output-on-failure
```
The Google Test suite (`mcm_tests`) covers representative inputs where the graph-based algorithms diverge (e.g., BHM vs. RAG-n vs. H_cub) and checks that the CSE hierarchy (Exact ILP, H2MC, H_CMVM) exhibits the expected ordering on a handcrafted CMVM instance.
