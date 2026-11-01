# Controls and the requirements they help evidence

What each control does, and the kind of requirement it helps evidence.

| Control | What it does | Helps evidence |
|---|---|---|
| `VerbaLedger` | Tamper-evident, hash-chained record of every gate decision | Record-keeping and logging (EU AI Act, ISO/IEC 42001, Qatar Central Bank AI Guideline) |
| `TerminalState` | A breach halts the agent | A way to stop the system (EU AI Act, NIST AI RMF) |
| `request_re_enablement()` | Back only with a named approver and evidence | Human oversight and accountability (EU AI Act, NIST AI RMF, Singapore IMDA) |
| `PreNode` | A prerequisite, such as an independent or human confirmation, checked before the action | Human approval at action boundaries (Singapore IMDA) |
| `Invariant` | Hard rules written by humans | Human-defined constraints (DIFC Regulation 10, Singapore IMDA) |
| `audit()` + certificate | Cross-checks the record; refuses a certificate on failure | Audit and traceability (ISO/IEC 42001, Qatar Central Bank) |

VSL-Core's [`governance-frameworks.md`](https://github.com/supersemantics/VSL-Core/blob/cb2f2d015a9ca9c0b4ca574e73e0dbe4f9ba7574/docs/governance-frameworks.md) goes further on the EU AI Act, NIST, ISO 42001 and IMDA. It doesn't cover DIFC or the Qatar Central Bank.

These controls produce evidence. They don't make a deployment compliant; an auditor decides that.
