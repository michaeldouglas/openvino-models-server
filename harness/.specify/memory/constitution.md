<!--
Sync Impact Report
- Version change: uninitialized scaffold -> 1.0.0
- Modified principles: none; the scaffold placeholders were replaced with the
  initial project principles.
- Added sections: Platform and Security Constraints; Development Workflow and
  Quality Gates.
- Removed sections: none.
- Follow-up TODOs: RATIFICATION_DATE remains TODO because the original adoption
  date is not available in the repository history.
-->

# FastAPI Docker Server Constitution

## Core Principles

### I. Skills-First Implementation
Every implementation decision MUST use the applicable installed project skill and
its `SKILL.md` instructions as the authoritative local workflow. A task MUST
identify the skills it uses, honor their prerequisites and safety constraints, and
record unresolved limitations rather than inventing unsupported behavior. When no
skill covers a decision, the implementation MUST document the assumption and its
rationale in the relevant design artifact.

### II. Explicit FastAPI Contracts
The server MUST expose a FastAPI application with explicit, typed request and
response contracts. Routes MUST define appropriate HTTP methods, status codes,
validation rules, and error responses; behavior that is not part of a documented
contract MUST NOT be treated as a public API. OpenAPI output MUST remain
consistent with the implemented routes and schemas. This keeps clients,
operators, and future changes aligned around a verifiable interface.

### III. Reproducible Containerization
The application MUST run through a versioned Docker build and a documented
container startup command. Builds MUST be reproducible from repository contents,
MUST use an explicit base image reference, and MUST keep runtime dependencies
separate from development-only dependencies when the chosen workflow supports
that distinction. Configuration MUST enter through documented environment
variables or mounted configuration, never through secrets committed to the
repository. The container MUST expose only the ports and processes required by
the service.

### IV. Test-First Quality
Each new or changed behavior MUST have automated tests at the narrowest useful
level, and every defect fix MUST include a regression test. API changes MUST
cover validation, successful responses, and relevant failure responses. The
containerized execution path MUST be verified by at least one integration or
smoke test before release. A change MUST NOT be considered complete while its
required tests fail or its acceptance criteria remain unverified.

### V. Observable and Safe Operations
The server MUST provide structured, actionable logs for startup, shutdown,
request failures, and operationally significant events without logging secrets or
full sensitive payloads. Health or readiness behavior MUST be explicit whenever
the service has dependencies that can prevent it from serving traffic. The
application MUST fail safely on invalid configuration, use least-privilege
runtime settings where supported, and return errors that are useful to clients
without exposing internal stack traces or credentials.

## Platform and Security Constraints

FastAPI and Docker are the baseline platform choices for the service. Python,
dependency, image, and server versions MUST be pinned or constrained in a
reviewable project artifact. The implementation MUST support environment-based
configuration, deterministic local startup, and a documented path for running
the service in Docker. Secrets MUST be supplied at runtime and MUST NOT appear in
source code, images, logs, test fixtures, or committed configuration. Any
additional dependency or infrastructure component MUST have a stated purpose,
an owner, and a verification method.

## Development Workflow and Quality Gates

Work MUST proceed from a written feature specification to an implementation plan
and an actionable task list before feature implementation begins. Each task MUST
identify affected contracts, tests, operational considerations, and applicable
skills. Review MUST verify constitution compliance, test evidence, configuration
handling, and Docker execution. Before merge or release, the project MUST run
the relevant automated tests, validate the FastAPI contract, and verify that the
documented container command starts the service successfully. Exceptions MUST be
written down with scope, rationale, risk, owner, and expiration or remediation
criteria.

## Governance

This constitution is the governing source for project-level engineering rules.
When another project document conflicts with it, the conflict MUST be resolved in
favor of this constitution or explicitly amended through the procedure below.

Amendments MUST be proposed with the affected principles, rationale, impact on
existing work, migration or adoption steps when needed, and updated compliance
checks. The change MUST be reviewed by the project owner or designated
maintainer, and the constitution MUST be updated in the same change set as its
approval record. Every implementation plan and review MUST check applicable
principles; deviations require the documented exception process above.

Versioning follows semantic versioning for governance: MAJOR for removing or
redefining a principle in a backward-incompatible way, MINOR for adding a
principle or materially expanding governance, and PATCH for clarifications,
wording, or non-semantic corrections. The version and last-amended date MUST be
updated whenever the constitution changes. A compliance review MUST occur for
each feature plan and before release, with failures resolved or recorded as an
approved exception.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): determine the original adoption date | **Last Amended**: 2026-09-06
