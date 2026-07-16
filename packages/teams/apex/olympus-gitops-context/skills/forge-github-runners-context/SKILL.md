---
name: forge-github-runners-context
description: Context on Flutter-Global's self-hosted GitHub Actions runner groups — how they are provisioned, named, declared in org-config, and referenced in workflows.
---

# Forge GitHub Runners Context

## What are runner groups?

Flutter-Global uses self-hosted GitHub Actions runners provisioned via **Forge ARC** (Actions Runner Controller). Runners are grouped by valuestream and provisioned in multiple instances for high availability.

Runner group access is declared in `org-config` via the `runner-groups:` field in a repository's codebase YAML. Codebase Governor (CBG) grants the repository access to those groups automatically when the org-config PR is merged — there is no separate CSV file or dashboard to update.

---

## Naming convention

Runner groups follow the pattern:

```
forge-arc-<valuestream>-prod-<n>
```

- `<valuestream>` — the owning valuestream (e.g., `gpcp`, `apex`, `gbp`)
- `<n>` — instance number, typically `1` and `2`

**Examples**:
- `forge-arc-gpcp-prod-1`
- `forge-arc-gpcp-prod-2`
- `forge-arc-apex-prod-1`
- `forge-arc-apex-prod-2`

> **GSCP/GPCP note**: These names refer to the same valuestream. GSCP is the Jira project key; GPCP is the platform/valuestream name. Runner groups for this valuestream are named `forge-arc-gpcp-prod-*`.

---

## Discover available runner groups

List all runner group directories in org-config to confirm which groups exist for a valuestream:

```bash
gh api repos/Flutter-Global/org-config/contents/runner-groups \
  --jq '.[].name'
```

Or search the codebases directory for a known repo from the same capability to infer the correct group name:

```bash
# Clone org-config, then grep for runner-groups in codebase YAMLs
ORG_CONFIG_TMP=$(mktemp -d)
gh repo clone Flutter-Global/org-config "$ORG_CONFIG_TMP" --depth 1 --quiet
grep -r "runner-groups" "$ORG_CONFIG_TMP/codebases/<capability>/"
```

---

## Declaring runner group access in org-config

Add a `runner-groups:` field to the repository's codebase YAML at `org-config/codebases/<capability>/<repo-name>.yml`:

```yaml
runner-groups:
  - forge-arc-<valuestream>-prod-1
  - forge-arc-<valuestream>-prod-2
```

Always declare both prod instances to ensure high availability.

### Where to add this field

- **App repo** (`<app-repo>.yml`): Add `runner-groups:` alongside the existing `apps:` and `org-secrets:` fields. Include in the Step 4 org-config PR.
- **Infra repo** (`<infra-repo>.yml`): Add `runner-groups:` to the new infra repo codebase YAML created in Step 5. Include it inline in that file.

### Example (app repo codebase YAML)

```yaml
description: My application repo

apps:
  - group-jira-app
  - fg-trufflehog

org-secrets:
  actions:
    - ORG_GS_GROUP_OLYMPUS_INFRA_SECRET

runner-groups:
  - forge-arc-gpcp-prod-1
  - forge-arc-gpcp-prod-2
```

---

## `runs-on` label in GitHub Actions workflows

In GitHub Actions workflows, `runs-on:` references runners by their **scale set name**, not the full runner group name:

```yaml
runs-on: <valuestream>   # e.g., gpcp, apex, gbp
```

The `runs-on` label matches the `runnerScaleSetName` configured in `forge-build-arc` — typically just the valuestream name. Confirm by checking an existing workflow in the same capability.

---

## Warning: missing runner group access

If a repository is not granted access to its runner group, workflow jobs queue indefinitely with **no error message**. If this happens:

1. Check whether `runner-groups:` is declared in the repo's org-config codebase YAML
2. Check whether the org-config PR has been merged and CBG has processed it
3. As a temporary workaround, change `runs-on:` to `ubuntu-latest` in the affected workflow while waiting for the PR to merge, then revert once access is confirmed

---

**Maintained By**: Apex Team
