---
name: gpd-release-readiness
description: Use when assessing whether a GPD service is ready for release by checking tests, deployment configuration, observability, and operational documentation.
---

# GPD Release Readiness

Assess a service against its release checklist and report concrete evidence, risks, and missing checks.

## Workflow

1. Identify the service, target environment, and planned release scope.
2. Inspect the repository's build, test, deployment, and monitoring configuration.
3. Run the fastest relevant validation commands before deeper checks.
4. Check rollback, alerting, dashboards, runbooks, and ownership details.
5. Separate confirmed evidence from assumptions and unresolved risks.
6. Return a concise readiness verdict with blocking issues and recommended follow-ups.

## Output

Include:

- Readiness verdict: ready, ready with risks, or not ready.
- Checks performed and their results.
- Blocking issues with file or command references.
- Non-blocking risks and suggested owners.
- The exact next steps required before release.

Do not claim a check passed unless its command or configuration provides evidence.

