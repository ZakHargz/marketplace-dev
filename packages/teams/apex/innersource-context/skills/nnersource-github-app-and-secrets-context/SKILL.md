---
name: innersource-github-app-and-secrets-context
description: How GitHub App credentials are stored and accessed in Flutter-Global workflows. Use when a workflow needs to authenticate as a GitHub App, when searching for a GitHub App's private key secret, or when a secret is not visible to a repo's GitHub Actions.
---

# GitHub App Credentials in Flutter-Global

## App ID vs Private Key

The **App ID** is public — retrieve it without any secret:

```bash
gh api apps/{app-slug} --jq '.id'
```

Store the App ID as a **repo variable** (not a secret, not hardcoded) — it is non-sensitive but not known until Codebase Governor (CBG) creates the app. Only the **private key** is sensitive and requires a secret.

---

## Step 1 — Search org-secrets/actions

All org-level GitHub Actions secrets are declared in:

```
Flutter-Global/org-config/org-secrets/actions/
```

One YAML file per secret. List them:

```bash
gh api repos/Flutter-Global/org-config/contents/org-secrets/actions \
  --jq '.[].name'
```

Search for the app's private key by looking for files whose name contains the app slug (hyphens → underscores) and a suffix such as `_PEM`, `_PK`, `_PRIVATE_KEY`, or `_KEY`.

Check the `visibility` field inside the matching file:

- `selected` — can be exposed to specific repos → follow Step 2
- `private` — restricted to org-config only; contact the secret's `owners` to discuss changing visibility

---

## Step 2 — Expose the secret to the repo (`visibility: selected`)

Use the `innersource-codebase-governor-context` skill to identify the repo's capability, then add the secret name to `org-secrets.actions` in the repo's codebase YAML and raise a PR to org-config:

```yaml
org-secrets:
  actions:
    - SECRET_NAME
```

---

## Step 3 — Secret not found in org-secrets/actions

The secret was likely added directly to the repo as a repo-level secret, or does not yet exist.

### Requesting temporary admin access

Repo secrets and repo variables typically require admin access to set, though the exact permissions required may vary by org policy. Request a 3-hour temporary admin window by raising an issue on `Flutter-Global/org-config` using the **Temporary Repository Administrator** template:

- **Repository name:** the target repo (e.g. `apex-marketplace`)
- **Reason:** brief description of what you need to set and why
- **Request Type:** `TEMP_ADMIN_REQUEST` (pre-selected)

Access auto-revokes after 3 hours. Close the issue early to revoke sooner.

### Repo secrets vs repo variables

| Value type | Storage | Workflow context | Command |
|---|---|---|---|
| Sensitive (private key, token) | Repo secret | `${{ secrets.NAME }}` | `gh secret set NAME --body "value" --repo org/repo` |
| Non-sensitive config (App ID) | Repo variable | `${{ vars.NAME }}` | `gh variable set NAME --body "value" --repo org/repo` |

App IDs are public and should be stored as repo variables, not secrets.

### Once access is granted

```bash
# Set a repo variable (non-sensitive, e.g. App ID)
gh variable set MY_APP_ID --body "1234567" --repo Flutter-Global/my-repo

# Set a repo secret (sensitive, e.g. private key)
gh secret set MY_APP_PRIVATE_KEY --body "$(cat private-key.pem)" --repo Flutter-Global/my-repo
```

After adding a repo secret it is good practice to also store the value in AWS Secrets Manager for durability. Discuss with the user which AWS account and path to use.

---

**Maintained By**: Apex Team
