# Changelog

## 0.1.2

**Before:** the setup line in scenes 12 and 14 was one character too long for its column, so it ran into the verdict: `...breached an invariantSETUP`.

**After:** the line is shorter, and a test checks that every line in every run fits its column.

**Why:** the terminal output is what readers see first.

**Requires:** nothing new.

## 0.1.1

Docs only. No change to the code or the demo's behaviour.

**Before:** `docs/scenes.md` said the film's shutdown was "unlogged" and that the airlock was the only path HAL didn't control. The film establishes neither. `docs/limits.md` didn't say what a fork's ledger or certificate is worth.

**After:** both scene lines say only what the film shows, and `docs/limits.md` says a ledger or certificate proves nothing about modified code.

**Why:** no invented film facts, and no reading more into a certificate than it says.

**Requires:** nothing new.

## 0.1.0

First version.

**Before:** nothing, beyond the MIT license.

**After:** a runnable replay of the HAL 9000 storyline against VSL-Core `cb2f2d0`: scripted HAL, three real gates, a terminal state, a hash-chained ledger, a human sign-off, a tamper demo, and a local web demo started with `hal9000-demo`.

**Why:** to make "scripted HAL, real VSL-Core gates and ledger" something anyone can check by running it.

**Requires:** `super-semantics-vsl` at commit `cb2f2d0`, from GitHub. It isn't on PyPI yet.
