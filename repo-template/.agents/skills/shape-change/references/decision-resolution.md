# Decision resolution

Classify one unresolved question and use the cheapest reliable procedure.

| Uncertainty | Procedure | Exit |
| --- | --- | --- |
| Repository fact | Inspect code, tests, history, context, and ADRs | Fact established |
| Routine reversible engineering choice | Follow repository evidence and choose | Choice recorded in plan or code when useful |
| External or version-sensitive fact | Check the primary source with bounded research | Cited fact and limitation |
| Measurable technical question | Run a throwaway prototype for one named question | Measurement recorded; prototype discarded or isolated |
| One consequential choice with several defensible answers | Simulate the smallest useful set of perspectives | Recommendation made; human chooses |

For simulated perspectives:

1. Choose only roles whose expertise, incentives, or risks differ materially.
2. State the strongest case and evidence standard for each.
3. Make perspectives respond to the real trade-off, not straw men.
4. Identify agreement, disagreement, and what evidence would change the answer.
5. Recommend a choice and state its cost.
6. Leave product policy and durable architecture decisions to the human.

Do not invoke a public `grill-me`, `simulate-discussion`, `ask-matt`, or
Wayfinder command. Focused questioning is part of shaping; these procedures are
loaded only when their signal exists.
