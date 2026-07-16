---
name: forge-store-jfrog-whitelist
description: How to add a GitHub repository to an existing JFrog OIDC module whitelist in forge-store-tf so that GitHub Actions workflows can authenticate with JFrog Artifactory via OIDC.
---

# Adding a Repository to the JFrog OIDC Whitelist (forge-store-tf)

## Background

Flutter-Global uses JFrog Artifactory (Forge Store) to store build artefacts including Helm OCI charts and container images. Access from GitHub Actions is granted via OIDC — no long-lived secrets are required.

Each valuestream has a module in `forge-store-tf` that declares which GitHub repositories are allowed to authenticate. If a repository is not in the whitelist, the CI workflow will receive a `403 Forbidden` from JFrog.

**Repository**: `Flutter-Global/forge-store-tf`
**Support channel**: `#gp-plat-eng-support` on Slack

---

## Requesting access via GitHub Issue

Onboarding is self-service via a GitHub Issue. The Forge/Sparta team handle the Terraform change on your behalf.

**Step 1** — Navigate to `Flutter-Global/forge-store-tf` → **Issues** → **New Issue**

**Step 2** — Select **"Request GitHub Repo access to Forge Store Artifactory Project"**

**Step 3** — Complete the form:

| Field | Value |
|---|---|
| **Artifactory Project** | The project key for your valuestream (e.g. `gpcp`) |
| **GitHub Organisation** | `Flutter-Global` |
| **GitHub Repositories** | List each repository requiring access, one per line — short name only (e.g. `apex-oncall-slack-bot-app`) |

**Step 4** — Submit the issue. Forge/Sparta will action it and notify you when complete.

---

## Verification

Once Forge/Sparta confirm the change is applied, re-run the failing CI workflow. The JFrog OIDC exchange should succeed and the 403 error should be gone.

If it still fails, check:
1. The `VALUE_STREAM` variable in the CI workflow matches the project key exactly (e.g. `gpcp`, not `apex`)
2. The repository short name submitted in the issue matches the repo name exactly (case-sensitive); the org is provided separately via the GitHub Organisation dropdown

---

## Related skills

- `forge-store-new-module` — use this instead if no Artifactory project exists yet for the valuestream
- `forge-github-runners-context` — for granting runner group access (separate concern from JFrog OIDC)

---

**Maintained By**: Apex Team
