# Reference answers

On GitHub, expand a question below to reveal a sample answer. These answers
use the recorded M5 Max runs with hypredrive v0.4.0 and hypre v3.2.1; exact timings and, sometimes, the fastest policy
depend on the machine. Compare your residual and explain your result using
your own measurements. The [M5 logs and summary](reference/macos-arm64-m5/summary.csv)
show the raw data; the [SPE10/MGR reference](reference/macos-arm64-m5/spe10/README.md)
has the eight-rank Lab 3 results.

## Lab 1: convergence and restart

<details>
<summary>1. Did every run reach the tolerance? A capped iteration count alone is not success.</summary>

Yes, all eight M5 reference runs reached the requested relative residual of
1e-8 or less. The residuals were 8.09e-9 for the Jacobi baseline; 5.99e-9,
5.68e-9 and 5.54e-9 for the 24-cubed PCG, GMRES(30) and BiCGSTAB runs; and
9.66e-9, 9.31e-9, 8.91e-9 and 9.69e-9 for the corresponding 48-cubed runs,
including GMRES(5). Check the residual in your own output rather than
inferring convergence from its iteration count.

</details>

<details>
<summary>2. How much does the matrix grow when each dimension doubles?</summary>

The unknown count grows by exactly eight: 24-cubed has 13,824 unknowns and
48-cubed has 110,592. For the same three-dimensional stencil, the nonzero
count also grows by about eight, with a small boundary effect.

</details>

<details>
<summary>3. Does a BiCGSTAB iteration cost the same as a PCG iteration?</summary>

No. A PCG step typically uses one matrix-vector product; a BiCGSTAB step
typically uses two, along with more vector operations and reductions. In the
48-cubed M5 runs, PCG took 105.268 ms for 60 iterations (about 1.75 ms per
iteration), while BiCGSTAB took 139.416 ms for 41 iterations (about 3.40 ms
per iteration).

</details>

<details>
<summary>4. What information does GMRES discard on restart? Compare 5 with 30.</summary>

GMRES stores an Arnoldi basis and the small least-squares problem built from
it. A restart discards that basis and starts a new Krylov space from the
latest solution. A smaller restart uses less memory, but can lose useful
directions and need more iterations. On the 48-cubed M5 case, GMRES(5) needed
188 iterations and 389.294 ms; GMRES(30) needed 79 iterations and 209.206 ms.
Both met the requested tolerance.

</details>

## Lab 2: AMG growth and hierarchy cost

<details>
<summary>1. Do AMG iterations increase as much as FSAI iterations with problem growth?</summary>

No, in these runs. PCG with FSAI rose from 33 iterations at 24-cubed to 60
at 48-cubed, while PCG with AMG took 7 iterations at both sizes. This is
evidence for this problem and these two sizes, not a proof of asymptotic
scaling.

</details>

<details>
<summary>2. Which hierarchy stores the least operator work?</summary>

Two aggressive-coarsening levels had the lowest operator complexity in the
M5 output: 1.218, compared with 1.351 for one level and 3.147 for none.
Operator complexity is the total operator nonzeros across the hierarchy
divided by the fine-grid operator nonzeros, so the smaller value means less
operator storage and work in the hierarchy.

</details>

<details>
<summary>3. Does the smallest iteration count give the best setup-plus-solve time?</summary>

No. With zero aggressive levels, AMG used the fewest iterations (7) but took
121.965 ms for setup plus solve. One aggressive level took 84.231 ms with 12
iterations; two levels took 87.199 ms with 17 iterations. The one-versus-two
level difference is small, so repeat close timings on your machine.

</details>

<details>
<summary>4. Would your recommendation change for many right-hand sides with reusable setup?</summary>

Compare setup + R times solve for R right-hand sides, assuming the setup is
reused and each solve has a similar cost. On the M5, one aggressive level is
fastest for one solve and remains fastest as R grows: for 20 right-hand sides
the totals are about 815 ms (one level), 962 ms (zero) and 1,066 ms (two).
Repeat this calculation with your own setup and solve timings.

</details>

## Lab 3: SPE10 Darcy flow with MGR

<details>
<summary>Reference interpretation: What changes when the reduced pressure problem uses two AMG cycles instead of one?</summary>

The split labels flux as F and retains pressure as the C field. MGR uses the
reduced pressure problem as its coarse problem; adding a second AMG cycle
makes that coarse solve stronger. In the eight-rank M5 run, one cycle
converged in 23 GMRES iterations with relative residual 9.97e-11 and
223.710 ms setup plus solve. Two cycles converged in 19 iterations with
residual 9.19e-11, but took 250.408 ms total. The extra cycle saved four
iterations but made this solve 26.698 ms slower overall. Both met the
requested 1e-10 tolerance. This run used 1,137,200 unknowns on a 2x2x2 MPI
partition.

</details>

## Lab 4: a real matrix from file

<details>
<summary>1. Do the metadata and loaded row count match the expected matrix?</summary>

Yes. Schmid/thermal1 has 82,654 rows and 574,458 nonzeros after symmetric
storage is expanded. All three M5 policy logs report those dimensions.

</details>

<details>
<summary>2. Have all policies converged to the requested residual tolerance? Do they reach the same relative error?</summary>

All three M5 runs reached relative residual below 1e-8: AMG/PCG had
8.68e-9, FSAI/PCG had 9.42e-9, and ILU/GMRES(50) had 9.95e-9. Their relative
solution errors were different: approximately 4.74e-8, 3.81e-6 and 4.66e-4,
respectively. A small residual does not by itself guarantee the same solution
error; the matrix conditioning and the error direction matter.

</details>

<details>
<summary>3. Which setup is cheapest? Which complete solver lifecycle is cheapest?</summary>

ILU setup is cheapest at 7.013 ms. AMG/PCG has the cheapest setup-plus-solve
time at 116.135 ms, compared with 841.572 ms for FSAI/PCG and 1,307.174 ms
for ILU/GMRES(50). These totals exclude matrix import and assembly.

</details>

<details>
<summary>4. For 20 right-hand sides, evaluate setup + 20 times solve. What assumption does this make?</summary>

Using the M5 measurements, the estimates are 693.830 ms for AMG/PCG,
13,012.820 ms for FSAI/PCG and 26,010.233 ms for ILU/GMRES(50). This assumes
the matrix and policy stay fixed, setup can be reused, and the solve time per
right-hand side stays comparable. It excludes import and assembly.

</details>

<details>
<summary>5. What would you need to know before transferring this choice to your matrix?</summary>

Check the matrix size, sparsity pattern, symmetry and definiteness, scaling
and conditioning, and whether the right-hand side and tolerance match your
application. Confirm that the chosen solver and preconditioner are valid for
those properties (for example, PCG requires an SPD system and a compatible
preconditioner). Also consider memory, hardware and MPI layout, the number
of right-hand sides, and whether setup can be reused. Compare convergence
and end-to-end cost on your own matrix; if a known solution is available,
check solution error as well as residual.

</details>
