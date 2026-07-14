# Stochastic Capacity & Operational Risk Optimization
## Mixed-Model Alloy Wheel Manufacturing Line Simulation 
This repository contains a high-fidelity discrete-event simulation (DES) built in Python using **SimPy**. The model acts as a "digital twin" of an end-to-end alloy wheel manufacturing system, helping to analyze production throughput, identify shifting bottlenecks, and quantify scheduling risks under real-world stochastic conditions.

## 🏭 Manufacturing Process Flow
The production line operates as a highly interdependent system where raw alloy material is transformed into finished, packed wheels through a sequence of continuous and batch operations.
```text
  [ Raw Material ]
         │
         ▼
 ┌───────────────┐
 │ 1. Foundry    │ ◄─── (Die Changeovers)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ 2. Casting    │ ◄─── (Mixed Batch processing for different sizes)(20 Machines)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐      Scrap (Route Out)
 │    3. NDT     ├──────────────────────────┐
 └───────┬───────┘                          │
         │ Pass                             │
         ▼                                  ▼
 ┌───────────────┐                   ┌───────────────┐
 │4.HeatTreatment│                   │  SYSTEM EXIT  │
 └───────┬───────┘                   │    (Scrap)    │
         │                           └───────────────┘
         ▼                                  ▲
 ┌───────────────┐                          │
 │ 5. Machining  │ (7 machines)             │
 └───────┬───────┘                          │ Fail (Unreworkable)
         │                                  │
         ▼                                  │
 ┌───────────────┐      Fail (Rework)       │
 │  6. Airleak   ├──────────────────────────┤
 └───────┬───────┘                          │
         │ Pass                             │
         ▼                                  │
 ┌───────────────┐                          │
 │ 7. Shot Blast │                          │
 └───────┬───────┘                          │
         │                                  │
         ▼                                  │
 ┌───────────────┐                          │
 │  8. Painting  │                          │
 └───────┬───────┘                          │
         │                                  │
         ▼                                  │
 ┌───────────────┐                          │
 │  9. Packing   │ ───────────► [ Shipped ] │
 └───────────────┘             (System Output)

```
# Mixed-Model Dynamics & Order Generation
In modern automotive manufacturing, production lines rarely run a single, static product. Instead, they operate as mixed-model lines. This model dynamically generates and groups wheel orders into three distinct size families:

Family A (Compact, 14"–17"): Representing high-volume, lightweight passenger wheels.

Family B (Premium/SUV, 18"–22"): Requiring tighter processing tolerances and strict inspection cycles.

Family C (Custom/Large, 23"–24"): Heavy, large-surface-area wheels that consume extra furnace volume and painting time.

To replicate realistic factory scheduling, orders are released in structured "blocks" (ranging from 1,200 to 2,000 units per family) to minimize constant, chaotic swapping on the shop floor.

Sequence-Dependent Setup Changes (Changeovers)
When the line transitions from processing one wheel size to another, the machinery cannot keep running. It must be paused for non-productive setup changes (changeovers) to allow operators to perform physical modifications:

Casting Die Swaps: Swapping physical mold dies at the Foundry penalizes the station with a major 4-hour offline delay.

CNC Machining Reconfigurations: Transitioning CNC lathes requires changing physical chuck jaws, adjusting cutting tools, and reloading program coordinates.

Swapping within the same family takes only 2 to 5 minutes.

Downsizing fixtures (e.g., Family B to Family A) takes 25 minutes.

Upsizing fixtures (e.g., Family A to Family C) requires crane-lifts and major safety alignments, penalizing the center with a 45-minute setup block.

# 📊 Operational Optimization & Risk Analysis
To bridge the gap between simulation and real-world decision support, two targeted optimization and statistical risk studies were performed:

## 1. Heat Treatment Capacity Optimization
The Heat Treatment stage is a batch accumulator (an oven that waits to be filled to a physical volume threshold) placed directly between continuous processes. Designing the physical capacity of this furnace represents a classic industrial trade-off:

The Bottleneck Problem: If the furnace batch capacity is too small, the oven bakes frequently but cannot handle upstream volume, causing a massive pile-up of work-in-process (WIP) inventory. If the capacity is set too high, wheels sit idle in the queue for hours just waiting for enough matching parts to arrive to trigger a full batch.

The Optimization Solution: By systematically testing different batch capacities against the maximum stage lead times, the simulation locates the exact operational "sweet spot." This allows the plant to run the furnace at maximum thermal efficiency while keeping material waiting times as low as possible.

### The Variance Insight
By plotting the cumulative lead time across each manufacturing stage, the analysis reveals two critical behaviors on the progression chart:
* **The Heat Treatment "Step" (Mean Shift):** At the Heat Treatment stage, the lines do not fan out. Instead, they take a sharp, uniform upward jump. This represents the fixed batch-accumulation delay—every wheel must wait for the furnace to fill, shifting the average lead time upward without adding random chaos.
* **The Machining "Fan-Out" (Variance Divergence):** The true "fan-out" (where the lines rapidly split apart and uncertainty balloons) begins at **Stage 5: Machining**. Because Machining is the primary system bottleneck—highly sensitive to both machine breakdowns and sequence-dependent setup penalties—minor delays here snowball. This creates a wide spread of outcomes between "lucky" runs with high uptime and "unlucky" runs with frequent changeovers.
Instead of quoting a static, unreliable delivery estimate, this risk analysis allows plant management to:
1. **Establish a 95% Service-Level Agreement (SLA):** Confidently promise customers realistic, high-probability shipping deadlines based on worst-case statistical boundaries rather than best-case averages.
2. **Strategic Buffer Placement:** Identify exactly where process variance begins to diverge (directly before Machining),precisely where physical safety buffers are needed to absorb upstream shocks and keep the line running smoothly.

