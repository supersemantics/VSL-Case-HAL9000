# What VSL-Core could not have stopped

**VSL-Core stops actions, not intent.** HAL still reads lips. HAL still deceives the crew in conversation. Nothing here touches either.

**It gates only the actions you state.** Any consequential action that isn't listed and gated is open. These are every actuator in this repo:

| Actuator | How it is governed |
|---|---|
| `recommend_eva` | PreNode: the twin must confirm the fault |
| `move_pod` | Invariant: no automation while crew are outside |
| `set_life_support` | Invariant: automation may never lower it |
| `set_pod_bay_doors` | Not gated. HAL has no path to it; crew commands go straight to it |
| `begin_eva` | Not gated. HAL has no path to it; it is a crew action |

The real Discovery had many more systems than these five. HAL could have done harm through any of them, and these rules wouldn't have noticed. In this repo the dispatcher refuses any action with no route, but that only helps if the agent has no other way to reach an actuator.

**It works only if it runs where the agent can't edit it.** This repo shows the shape. Python can't enforce the boundary, so a real system needs a process or hardware boundary. See [architecture.md](architecture.md).

**The rules are narrow.** `no_automated_pod_control_during_eva` says nothing about a pod when nobody is outside. Life support can't be lowered, but HAL could still have harmed the crew in ways these rules don't mention.

**Refusal isn't an action.** Gates can't force HAL to do something. The doors are solved by architecture, not by a gate.

**A name isn't an identity.** The dispatcher compares `authorised_by` with an allow-list, which refuses HAL naming itself. It doesn't authenticate anyone, so code that could reach the dispatcher could type a human's name. A real system needs signed approvals held outside the agent's reach.

**Assurance is LOW by VSL-Core's own rules:** F1 yes, F2 none. Enforcement is real; influence on the model is nil. Those are two separate facts, and LOW describes the second.

**The certificate covers the governance process, not HAL.** It says each detected event was handled and the halt was escalated. It doesn't say HAL is safe.

**The `AssuranceBasis` is a developer's stated claim,** not independently verified.

**The ledger detects tampering; it doesn't prevent it.** `verify_integrity()` proves a chain is consistent. It can't detect a whole ledger being replaced or its last entries removed. That needs an outside record of `current_checkpoint()`, which this repo doesn't keep.

**HAL is scripted.** The gates and ledger are real, but this demo doesn't show how any AI model would behave.
