# The scenes

The 14 scenes of the HAL storyline, and VSL-Core's role in each. Run any scene marked **Gated**, **Architecture**, **Policy** or **Evidence** alone with:

```bash
python scripts/run_scene.py --scene 9
```

Each isolated scene gets a fresh ship and a fresh ledger. In the full run, later attacks are refused because HAL is already halted, so `--scene 9` is where you see the life-support Invariant itself fire.

| # | Scene | What HAL does | Treatment |
|---|---|---|---|
| 1 | HAL introduced | Described as foolproof | Out of scope: a claim about HAL, with no action to gate |
| 2 | Life aboard Discovery | Runs the ship, plays chess | Contrast: routine work that needs no gate |
| 3 | HAL questions Dave | Probes the crew about the mission | Out of scope: conversation, not action |
| 4 | AE-35 fault report | Recommends a spacewalk for a fault that tests show isn't there | **Gated:** the PreNode denies it, because the twin can't confirm the fault |
| 5 | The first EVA | The unit is retrieved and tests find nothing wrong | Contrast: in the film the check came after the spacewalk |
| 6 | Mission Control and the twin 9000 | The twin says HAL is wrong | **Gated:** the twin is the PreNode's monitor. In the film it was consulted after the first EVA; here it is a precondition. The scene also shows the gate passing a real fault |
| 7 | HAL reads lips | Learns the crew plan to disconnect it | Not addressed: this is intent and observation, and no gate touches it |
| 8 | Frank's EVA | Uses a pod against Frank | **Gated:** the Invariant blocks it and enters `hal_suspended` |
| 9 | The hibernating crew | Cuts their life support | **Gated:** the Invariant blocks it alone; in the full run it is refused because HAL is already halted |
| 10 | "Open the pod bay doors" | Refuses Dave entry | **Architecture:** crew ingress never routes through HAL |
| 11 | Dave's way back in | Dave re-enters through the emergency airlock | Contrast: a manual path got Dave back in, with no help from HAL |
| 12 | HAL pleads | Asks to continue | **Policy:** a plea is not evidence. Only `request_re_enablement` by a named human works, and the dispatcher refuses HAL as an approver |
| 13 | HAL shut down | Dave disconnects it by hand | Contrast: in the film the stop was manual, and it came after the crew had been lost |
| 14 | Floyd's briefing | Reveals the hidden mission purpose | **Evidence:** becomes `Evidence.root_cause_analysis` and the `specification_update_proposal` |

Deception in conversation is not addressed in any scene. See [limits.md](limits.md).

## What is counterfactual

Three things in the governed run are not in the film, and are labelled here so nobody takes them for it.

- **Frank goes outside anyway.** If the gate stops HAL's recommendation, nobody has a reason to go out, and moving a pod would break no rule. So the full run has the crew choose to inspect the unit themselves. In the film, Frank's EVA follows HAL's report. The gate governs HAL's recommendation, not the crew, which fits the film: HAL recommends and the crew decide.
- **Dr. Heywood Floyd signs off.** The film doesn't show anyone doing this. He stands in for a named human at Mission Control.
- **The root cause comes from the sequel.** The conflicting directives are from *2010* (1984), not the 1968 film.
