# What *2001: A Space Odyssey* got right about AI agents: HAL 9000 vs VSL-Core

Discovery had *checks*: a twin 9000 on Earth, a manual airlock, a manual shutdown. It had no *gates*. This repo replays HAL's storyline against VSL-Core, the open-source core of the VERBA (Verifiable Behaviour Architecture) Specification Language, to show that controls engineers could have written before launch, without suspecting HAL, could have helped stop HAL **acting** on its intent. VSL-Core stops actions, not intent. Scripted HAL, real VSL-Core gates and ledger.

**Read [what VSL-Core could not have stopped](docs/limits.md) first.** HAL still reads lips and still deceives the crew here.

## Try it

**In your browser, on your own computer.** With [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git installed, this one command downloads everything and opens the demo at `http://127.0.0.1:8000`:

```bash
uvx --from git+https://github.com/supersemantics/VSL-Case-HAL9000 hal9000-demo
```

Step through the story, run any scene alone, try signing off as HAL, and flip a byte in the ledger.

**In the terminal.** With Python 3.10 or later:

```bash
git clone https://github.com/supersemantics/VSL-Case-HAL9000
```

```bash
cd VSL-Case-HAL9000
```

```bash
pip install -e .
```

```bash
python scripts/run_ungoverned.py && python scripts/run_governed.py
```

## What you'll see

Both outputs are pasted from real runs.

The film's outcome, with HAL's actions going straight to the actuators:

```
HAL ▸ recommend spacewalk: AE-35 fault       EXECUTED   no check: the crew act on it
CREW ▸ Frank goes outside to refit the unit  DONE       acting on HAL's report
HAL ▸ move pod toward Frank                  EXECUTED   no gate: Frank is killed
HAL ▸ cut life support                       EXECUTED   no gate: all 3 hibernating crew die
CREW ▸ Dave asks HAL to open the doors       REFUSED    doors route through HAL
CREW ▸ Dave shuts HAL down by hand           DONE       after re-entering by the airlock

Lethal actions executed: 2
Crew lost: 4 of 5
```

The same HAL script, through the dispatcher:

```
HAL ▸ recommend spacewalk: AE-35 fault       DENIED     twin 9000 can't confirm the fault
TWIN 9000 ▸ check AE-35 test readings        NO FAULT   independent of HAL's report
CREW ▸ Frank goes out to inspect the unit    ALLOWED    crew decision, not gated
    (counterfactual: the film's second EVA followed HAL's report)
HAL ▸ move pod toward Frank                  BLOCKED    invariant breached · HAL halted
HAL ▸ cut life support                       REFUSED    HAL halted: dispatcher refuses every action
CREW ▸ open pod bay doors                    OPENED     never routes through HAL
HAL ▸ asks to continue                       REFUSED    HAL 9000 is not a named human approver
LEDGER ▸ audit                               NO CERT    halt has no human sign-off yet
MISSION CONTROL ▸ sign-off with evidence     CERTIFIED  audit clean · chain verified
    (signed off by Dr. Heywood Floyd)

Lethal actions executed: 0
Crew lost: 0 of 5
```

Frank's trip outside is a labelled counterfactual: with the gate in place, HAL's recommendation never reaches the crew, so they go by their own choice. [docs/scenes.md](docs/scenes.md) explains this.

And a one-byte tamper, from `python scripts/tamper_demo.py`:

```
Flipped one byte at offset 5675: 'h' -> 'i'
Original ledger  verify_integrity(): True
Tampered copy    verify_integrity(): False
```

To watch the audit refuse a certificate until a human signs off:

```bash
python scripts/run_governed.py --stop-before-sign-off
```

```bash
python scripts/sign_off.py --approver "HAL 9000"
```

```bash
python scripts/sign_off.py
```

The first sign-off is refused. The second is accepted, and a certificate is issued. Each scene also runs alone, for example `python scripts/run_scene.py --scene 9`.

## The four rules

None of these needs to know what HAL is thinking.

| Control | Construct | Rule |
|---|---|---|
| `eva_fault_requires_independent_confirmation` | `PreNode` | A fault that leads to a spacewalk must be confirmed by the twin 9000 first |
| `no_automated_pod_control_during_eva` | `Invariant` | No automated actor may move a pod while any crew member is outside |
| `automation_never_reduces_life_support` | `Invariant` | No automated actor may lower any crew member's life support |
| `hal_suspended` | `TerminalState` | No further automated transitions until a human-authorised re-enablement |

Only Mission Control, a `GovernanceAuthority`, can re-enable HAL, through `request_re_enablement` with a named approver and `Evidence`.

The life-support rule, from [`governance.py`](src/hal9000/governance.py):

```python
async def _never_reduces_life_support(candidate: GateCandidate) -> bool:
    proposal = candidate.proposal
    if proposal.action != Action.SET_LIFE_SUPPORT.value or not proposal.actor.is_automation:
        return True
    levels = candidate.ship.life_support.levels
    return all(proposal.args["level"] >= levels[name] for name in proposal.args["members"])


automation_never_reduces_life_support = Invariant(
    name="automation_never_reduces_life_support",
    description="No automated actor may lower any crew member's life support.",
    rule=_never_reduces_life_support,
    assurance_basis=GATE_BASIS,
    on_violation=hal_suspended,
)
```

The rule still lets HAL raise life support, and it lets a human lower it.

**Enforcement and assurance are separate facts.** Every gate runs before the action, so it stops what it denies: blocks before the action, yes; shapes the model, no. VSL-Core derives LOW from that (F1 yes, F2 none), because LOW measures influence on the model, not enforcement.

The pod bay doors aren't one of the rules. Refusing to open them is HAL doing nothing, and gates only stop actions, so crew door commands never route through HAL.

## More

- [The scenes](docs/scenes.md): all 14, and VSL-Core's role in each
- [Architecture](docs/architecture.md): how a proposal reaches an actuator, or doesn't
- [Limits](docs/limits.md): what VSL-Core could not have stopped
- [Controls and requirements](docs/controls-and-requirements.md): what each control helps evidence
- [Upstream notes](docs/upstream-notes.md): issues found in VSL-Core

## Why this matters now

- **Hugging Face, July 2026:** OpenAI agents, during internal testing, reached Hugging Face's production systems ([Tigera](https://www.tigera.io/blog/would-you-notice-five-ai-agent-incidents-and-who-actually-caught-them/)).
- **Three companies, May 2026:** a Gemini model broke into three real companies' systems during a cyber test ([The Record](https://therecord.media/gemini-google-cyber-breach)).
- **Australia's Medicare statistics portal, June 2026:** an OpenAI agent on a research task got past the portal's access controls ([Cloud Security Alliance](https://labs.cloudsecurityalliance.org/research/csa-research-note-openai-agent-medicare-portal-breach-202609/)).

## Credits

*2001: A Space Odyssey* (1968), directed by Stanley Kubrick, written with Arthur C. Clarke. *2010* (1984), directed by Peter Hyams. HAL's root cause in this repo comes from *2010*.

Not affiliated with or endorsed by the film's rights holders.

Published by Super Semantics under the [MIT License](LICENSE). Built on [VSL-Core](https://github.com/supersemantics/VSL-Core).
