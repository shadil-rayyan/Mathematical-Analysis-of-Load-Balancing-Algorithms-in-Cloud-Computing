Mission
Complete a reproducible mini-project that models jobs arriving at a fixed pool of identical servers and compares:
1. Uniform random assignment: send each job to one uniformly random server.
2. Power of Two Choices (P2C): sample two distinct servers uniformly at random and send the job to the currently less-loaded server; break ties randomly.
The project must connect the simulation to counting, probability, expectation, and the balls-and-bins model. Do not invent results: run the simulation, calculate the metrics from the output, and discuss results actually observed.
Expected deliverables
Create the following files in the project directory:
- report.md — a student-ready report with model, assumptions, mathematics, experimental setup, plots, results, interpretation, limitations, and references.
- simulation.py — reproducible implementation of both allocation policies and all experiments.
- results/summary.csv — one row per policy/configuration with measured statistics.
- results/plots/maximum_load.png — distribution of maximum server load across independent trials for each policy/configuration.
- results/plots/load_distribution.png — server-load distribution for each policy in a clearly named representative configuration.
- results/plots/overload_rate.png — empirical probability that any server becomes overloaded, with the overload threshold stated on the figure or in its caption.
- README.md — commands to install dependencies and reproduce the results.
Use Python 3.10+ and common packages (numpy, pandas, matplotlib). Keep the program understandable for an undergraduate probability / cloud-computing project. Avoid unnecessary frameworks.
Formal model
Let:
- S = number of servers, with S >= 2.
- J = number of jobs assigned sequentially.
- L_i = number of jobs assigned to server i after all J jobs have been assigned.
- lambda = J / S = average load per server.
- M = max(L_1, ..., L_S) = maximum load.
Base assumptions
- Servers have equal capacity and are treated as identical.
- Every job has unit size and remains assigned for the entire experiment; no jobs finish or leave.
- Jobs arrive one at a time, and each allocation decision is made before the next job is assigned.
- The base model measures load by job count, not execution time, CPU, memory, or queueing delay.
- The random server choices are uniform. P2C samples two distinct servers without replacement.
- P2C reads the current simulated load exactly. The report must explain that real systems can have stale or delayed measurements.
State clearly that these assumptions make this an allocation / balls-and-bins model, not a full queueing simulator.
Overload definition
For each configuration, define a comparison threshold

C = ceil(1.5 * lambda).

A server is overloaded if L_i > C; an experiment is overloaded if at least one server is overloaded (M > C). This is a project-specific operational threshold, not a universal cloud-service standard. Repeat the same definition for both policies and print lambda and C in the report and relevant plot captions.
Allocation algorithms
Policy A — Uniform random
For each incoming job, independently select a server uniformly from {1, ..., S} and increment its load by one.
Policy B — Power of Two Choices
For each incoming job:
1. Sample two distinct servers uniformly from {1, ..., S}.
2. Compare their current loads.
3. Assign the job to the server with smaller load.
4. If the loads tie, pick either sampled server with probability one-half.
5. Increment the chosen server's load by one.
Implement both policies as separate, testable functions. Make clear that P2C is sequential and sees the current simulated loads; concurrent real-world dispatchers may not have that information.
Experimental design
Run at least the following four configurations:
Label	Servers S	Jobs J	Mean load lambda = J/S	Purpose
Balanced benchmark	100	100	1	Connect to the classic J = S balls-and-bins result.
Small pool	10	100	10	Demonstrate allocation variability in a small pool.
Medium pool	50	500	10	Compare with the small pool at the same mean load.
Heavy workload	50	2500	50	Show how results change as workload per server increases.


Use at least 500 independent trials per policy per configuration; 1,000 is preferred if runtime is reasonable. Set and document a fixed master seed (for example, 20261029) so results can be reproduced. Use independently initialized pseudo-random generators for each trial/policy, and do not change the seed silently between runs.

For every trial, record at least:
- maximum load M;
- mean server load;
- standard deviation of server loads;
- overloaded-server count;
- overloaded-system indicator (M > C).
Summarize across trials for each configuration/policy:
- mean and median maximum load;
- 95th percentile maximum load;
- average server-load standard deviation;
- empirical overload probability (fraction of trials where any server has L_i > C);
- empirical mean load, as a sanity check against J/S.
Do not report only one lucky run. The unit of replication is a whole allocation experiment, not an individual job.
Mathematical analysis to include in report.md
Expected load
For uniform random assignment, each server receives each job with probability 1/S, independently across jobs. Therefore

L_i ~ Binomial(J, 1/S)

and

E[L_i] = J/S = lambda,

Var(L_i) = J(1/S)(1 - 1/S).

For P2C, the server labels are symmetric and exactly J jobs are assigned, so the expected load of each server is also E[L_i] = J/S. Explain the important point: equal expected loads do not mean equally balanced realized loads. The main comparison is the tail / maximum load and variability, not the average load alone.
A probability bound for random assignment
For a fixed server, L_i ~ Binomial(J, 1/S). For an integer threshold k, use the union bound:

P(M >= k) <= S * P(Binomial(J, 1/S) >= k).

The binomial tail can be evaluated directly for these modest experiment sizes. Also show the Chernoff form when k > lambda:

P(M >= k) <= min(1, S * exp(-lambda * h(k/lambda))),

where h(r) = 1 - r + r * ln(r) for r > 1.

Use k = C + 1 to bound the probability of overload under the project definition (M > C). Handle edge cases safely, such as k > J, when the event is impossible. Check the expression numerically before putting it in the report. Describe it as an upper bound, not the true probability.

Do not claim the same simple binomial-tail expression for P2C: server loads are dependent under P2C. For P2C, use the measured simulation probability and discuss the known asymptotic result below.
Classic balls-and-bins result
For the classic case with J = S = n and equal-size jobs, the maximum load under one random choice is of order ln(n) / ln(ln(n)) with high probability. Under two choices, the maximum load is of order ln(ln(n)); a commonly cited leading expression is ln(ln(n)) / ln(2) + O(1) with high probability, under the classic model. Cite Azar, Broder, Karlin, and Upfal (1999).

Make the scope explicit: this is an asymptotic theorem, not an exact prediction for every finite configuration, and it applies directly to the balanced J = S benchmark rather than automatically to all workload ratios. Use it to explain why sampling only two candidates can have a large effect on the maximum load.
Plot requirements
Use legible axes, titles, legends, and units. Keep policy colors consistent across figures. Do not combine plots in a way that hides differences between configurations.
1. Maximum load: boxplots or violin plots of maximum load across independent trials, grouped by policy and configuration. Include the average-load lambda in the tick label or caption so comparisons are not misleading.
2. Load distribution: show the distribution of individual server loads from a clearly identified configuration. A histogram, empirical cumulative distribution, or side-by-side boxplots of server loads are acceptable. State whether values are from one trial or pooled over trials; pooled values must not be described as independent trials.
3. Overload probability: show the empirical overload rate for both policies/configurations. Label the overload rule M > ceil(1.5 * J/S). If no overload was observed, report zero observed events out of R trials rather than implying the true probability is zero. Optionally give the rule-of-three approximation 3/R as a rough 95% upper limit after zero events.
Save figures as PNGs in results/plots/ and reference them from report.md using relative paths.
Practical trade-offs to discuss
The discussion must be balanced; do not claim P2C is always better in production.
- Probe / coordination overhead: random assignment needs no load measurement; P2C usually needs two load probes or a source of recent load estimates.
- Stale information and concurrency: simultaneous dispatchers may read the same server as lightly loaded and send it many jobs. Extra coordination/telemetry has latency and cost. Cited work on stale load information shows why the age of load information matters.
- Uneven job sizes: job count can be a poor proxy for CPU time, memory, or completion time. If a small extension is practical, simulate non-unit job sizes and compare count-based P2C with size-aware assignment, but clearly state what information the dispatcher knows at assignment time. Do not mix this extension into the unit-size theoretical formulas without explanation.
- Different server capacities: identical-server assumptions may fail. A practical policy may need capacity-weighted load rather than raw job count.
- Operational decision: P2C is attractive when imbalance is costly and load signals are cheap and fresh; simple random (or round-robin) may be sufficient for homogeneous, similarly sized requests where lower overhead and simpler operations matter.
Use AWS's load-balancing guidance only as a real-world illustration, not as evidence for the mathematical theorem. AWS documentation distinguishes round robin for similar requests from least-outstanding-requests routing when request complexity or backend latency varies.
Report outline
1. Title, objective, and syllabus connection (Modules 2 and 4; CO2 and CO4, as supplied in the project brief).
2. Application motivation: distributing jobs across cloud servers.
3. Formal model, assumptions, load, maximum load, and overload.
4. Algorithms / pseudocode.
5. Mathematical analysis: expectation, variance for random allocation, union/Chernoff bound, and classic P2C result with caveats.
6. Simulation setup: configurations, trials, seed, metrics, and implementation.
7. Results: summary table plus required plots.
8. Interpretation: what changed, what did not, and why the maximum differs even when mean load is the same.
9. Operational trade-offs, limitations, and possible improvements.
10. Conclusion.
11. References with author/title/year and working links.
Keep the writing direct and undergraduate-appropriate. Clearly distinguish theoretical results, simulated observations, and interpretation. Do not fabricate output values, claim a simulation was run unless it actually was, or describe a small finite sample as proof.
Research sources
Use and cite at least three relevant sources. Start with these:
1. Y. Azar, A. Z. Broder, A. R. Karlin, and E. Upfal, “Balanced Allocations,” SIAM Journal on Computing, 29(1), 180–200 (1999). DOI: https://doi.org/10.1137/S0097539795288490. A publisher / research entry is available at https://research.ibm.com/publications/balanced-allocations and the paper abstract is available at https://epubs.siam.org/doi/abs/10.1137/S0097539795288490.
2. Michael Mitzenmacher and Eli Upfal, Probability and Computing: Randomization and Probabilistic Techniques in Algorithms and Data Analysis, 2nd ed., Cambridge University Press (2017), Chapter 17, “Balanced Allocations and Cuckoo Hashing.” Publisher information: https://www.cambridge.org/core/books/probability-and-computing/3A5B47DB315FC64B9256C5C8131C5EFA. A course/textbook PDF containing a chapter titled “Balanced Allocations” is also available at https://www.cs.purdue.edu/homes/spa/courses/pg17/mu-book.pdf. Check which edition/chapter is represented in the PDF before citing a chapter number.
3. Elias Koutsoupias, Probability and Computing course notes: “Balls and bins — maximum load,” University of Oxford: https://www.cs.ox.ac.uk/people/elias.koutsoupias/pc2018-19/lectures.html
- Every external factual claim is cited; bibliography links are accessible.
