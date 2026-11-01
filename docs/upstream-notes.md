# Notes for VSL-Core

Found while building this repo against `cb2f2d0`. VSL-Core wasn't changed; each item is handled here.

## Reference adapter hard-codes its identity

`PlainPythonReferenceAdapter` raises with `identity_key="conformance-test"`, so a denial can't be traced to the agent it came from. Anyone who copies it as a starting point inherits that.

**Here:** `HalAdapter(identity_key, instance_id)` raises with the real identity and passes `run_conformance_suite`.

## Stale EU AI Act date in `governance-frameworks.md`

Line 241 says the high-risk obligations "activate 2 August 2026". The Digital Omnibus on AI, Regulation (EU) 2026/1744, moved stand-alone Annex III high-risk systems to 2 December 2027 and systems embedded in Annex I products to 2 August 2028. The dates here come from secondary sources, such as [Gibson Dunn](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/) and the [European Parliament's legislative train](https://www.europarl.europa.eu/legislative-train/package-digital-package/file-digital-omnibus-on-ai). Check the Official Journal text before changing the document.

## `authorised_by` accepts any non-empty name

`request_re_enablement(..., authorised_by="HAL 9000", ...)` succeeds. `HumanAuthorisedTransition` checks only that the string isn't empty, although its error message says "a real, non-empty human approver".

**Here:** the dispatcher checks an allow-list before calling it. An identity check is the real answer, and that sits outside VSL-Core's scope, so the docstring could say so.

## Gate callers can't see the estimate

A compiled gate raises or returns `None`, but `write_gate_decision` needs the monitor's `GammaEstimate`. The README's answer is to write the record inside the monitor. That couples the monitor to the ledger, and it can't write the rest of the chain.

**Here:** `GateCandidate` carries the estimate back to the dispatcher, so the twin is asked once and the dispatcher writes every entry.

## The distribution name differs from the repo and import names

The repo is `VSL-Core`, the import is `vsl_core`, and the distribution is `super-semantics-vsl`. So `pip install "vsl-core @ git+..."` fails with a metadata name mismatch. `pyproject.toml` here uses `super-semantics-vsl @ git+...`. An install line in VSL-Core's README would help.
