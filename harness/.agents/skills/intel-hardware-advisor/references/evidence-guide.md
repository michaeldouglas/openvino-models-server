# Evidence Guide

The advisor uses these evidence classes:

- `detected`: observed by a local collector, such as the host platform or an
  OpenVINO runtime response.
- `documented`: stated by an authoritative vendor or runtime document with
  version and scope recorded.
- `measured`: produced by a reproducible workload measurement.
- `estimate`: a derived value with assumptions exposed.
- `inference`: a reasoned conclusion that must not be presented as a detected
  capability.

The report may also expose lightweight configuration statuses: `configured`,
`incomplete`, `not_checked`, and `not_applicable`. These describe what the
portable probe could observe; they do not replace versioned driver or workload
documentation.

For the first release, local detection is enough to say that a runtime sees a
device. It is not enough to say that a particular model, precision, driver, or
performance target is supported. Those conclusions need evidence whose version,
hardware scope, and limitations match the claim.

When evidence is incomplete or contradictory, preserve the facts and return
`decision: no_decision`. Recommend the smallest safe verification step rather
than guessing.
