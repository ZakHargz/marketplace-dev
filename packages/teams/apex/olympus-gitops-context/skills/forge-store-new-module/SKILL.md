---
name: forge-store-new-module
description: How to request a new Forge Store local repository for a valuestream via a GitHub Issue. Use forge-store-jfrog-whitelist instead if the repository already exists and you only need OIDC access.
---

# Requesting a New Forge Store Local Repository

## When to use this skill

Use this skill when no Artifactory project exists yet for the valuestream in Forge Store. If the project already exists (e.g. `gpcp`), use the `forge-store-jfrog-whitelist` skill to add a repository to the existing whitelist instead.

**Repository**: `Flutter-Global/forge-store-tf`
**Support channel**: `#gp-plat-eng-support` on Slack

---

## Background

Each valuestream that needs to push artefacts to JFrog Artifactory via GitHub Actions OIDC requires a local repository provisioned in Forge Store. This is a one-time setup per valuestream, performed by the Forge/Sparta team.

---

## Requesting a new local repository via GitHub Issue

Onboarding is self-service via a GitHub Issue. The Forge/Sparta team handle the provisioning on your behalf.

**Step 1** — Navigate to `Flutter-Global/forge-store-tf` → **Issues** → **New Issue**

**Step 2** — Select **"Request Forge Store Local Repository"**

**Step 3** — Complete the form:

| Field | Value |
|---|---|
| **Artifactory Project** | The project key for your valuestream (e.g. `gpcp`) |
| **Package Type** | The artifact type the repository will store (e.g. `helm`, `container`, `npm`) |
| **Justification** | Explain what the repository is for and why it is needed |

**Step 4** — Submit the issue. Forge/Sparta will action it and notify you when complete.

---

## After the repository is provisioned

Once Forge/Sparta confirm the local repository has been created, use the `forge-store-jfrog-whitelist` skill to request OIDC access for your GitHub repositories.

---

## Related skills

- `forge-store-jfrog-whitelist` — request OIDC access for a GitHub repository to an existing Artifactory project

---

**Maintained By**: Apex Team
