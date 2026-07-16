---
name: olympus-app-of-apps
description: How to register a new application with Olympus ArgoCD clusters by adding an entry to the Flutter-Global/olympus-app-of-apps repository. Use this skill when bootstrapping ArgoCD for a new application or environment for the first time.
---

# Registering an Application in Olympus App-of-Apps

## Background

ArgoCD on each Olympus cluster watches a single root Application called `app-of-apps`. That root Application points at `Flutter-Global/olympus-app-of-apps`, which contains one YAML file per registered application. When a new file is added and the PR is merged, ArgoCD auto-syncs and creates the outer Application within ~1–2 minutes — no manual `kubectl apply` or `argocd app create` is required.

**Repository**: `Flutter-Global/olympus-app-of-apps`
**No special approval gating** — a standard PR review and merge is sufficient.

---

## Directory Structure

The repo is organised by cluster name. Each cluster directory contains two items:

```
<valuestream>-<env>-argocd/
├── app-of-apps.yml          # root Application — DO NOT EDIT
└── app-of-apps/
    ├── existing-app.yml
    └── your-new-app.yml     # <-- add your file here
```

The cluster naming pattern is:

```
<valuestream>-<env>-argocd
```

Examples:
- `apex-stg-argocd`
- `apex-prd-argocd`
- `ops-channel-stg-argocd`
- `gpcp-stg-argocd`

To list all available cluster directories:

```bash
gh api --paginate repos/Flutter-Global/olympus-app-of-apps/contents --jq '.[].name'
```

---

## YAML Format

Each application registration file uses the `sources:` (plural) format pointing to the infra repo's `argocd-apps/<env>/` directory:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  destination:
    namespace: argocd
    name: in-cluster
  project: applications
  sources:
    - repoURL: https://github.com/Flutter-Global/<infra-repo>
      path: argocd-apps/<env>
      targetRevision: main
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
```

**Key fields:**

| Field | Value | Notes |
|---|---|---|
| `metadata.name` | `<app-name>` | Use the chart/app name with no environment suffix — e.g. `apex-oncall-slack-bot`, not `apex-oncall-slack-bot-stg` |
| `destination.name` | `in-cluster` | ArgoCD deploys to the same cluster it runs on |
| `destination.namespace` | `argocd` | The outer Application lives in the ArgoCD namespace |
| `sources[0].repoURL` | infra repo URL | Full GitHub URL to `Flutter-Global/<infra-repo>` |
| `sources[0].path` | `argocd-apps/<env>` | Points to the directory in the infra repo that contains the inner Application manifests |
| `sources[0].targetRevision` | `main` | Outer app always tracks the default branch |

**What `path: argocd-apps/stg` points to in the infra repo:**

```
apex-oncall-slack-bot-infra/
└── argocd-apps/
    └── stg/
        └── apex-oncall-slack-bot-stg.yaml   # <-- inner Application; ArgoCD applies this
```

---

## Step-by-Step Process

### Step 1 — Clone olympus-app-of-apps

```bash
APP_OF_APPS=$(mktemp -d)
echo "Cloning olympus-app-of-apps into $APP_OF_APPS ..."
gh repo clone Flutter-Global/olympus-app-of-apps "$APP_OF_APPS"
cd "$APP_OF_APPS"
```

### Step 2 — Create a feature branch

```bash
git checkout -b gscp-XXXX-add-<app-name>-to-app-of-apps
```

### Step 3 — Create the registration file(s)

Create one file per environment. Both stg and prd can be added in the same PR.

**Staging:**

```bash
cat > <valuestream>-stg-argocd/app-of-apps/<app-name>.yml <<'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  destination:
    namespace: argocd
    name: in-cluster
  project: applications
  sources:
    - repoURL: https://github.com/Flutter-Global/<infra-repo>
      path: argocd-apps/stg
      targetRevision: main
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
EOF
```

**Production** (add when ready):

```bash
cat > <valuestream>-prd-argocd/app-of-apps/<app-name>.yml <<'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  destination:
    namespace: argocd
    name: in-cluster
  project: applications
  sources:
    - repoURL: https://github.com/Flutter-Global/<infra-repo>
      path: argocd-apps/prd
      targetRevision: main
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
EOF
```

### Step 4 — Commit and push

```bash
git add <valuestream>-stg-argocd/app-of-apps/<app-name>.yml
# git add <valuestream>-prd-argocd/app-of-apps/<app-name>.yml  # include if adding prd at the same time
git commit -m "feat(app-of-apps): [GSCP-XXXX] - Add <app-name> to <valuestream> clusters"
git push origin gscp-XXXX-add-<app-name>-to-app-of-apps
```

### Step 5 — Raise a Pull Request

```bash
gh pr create \
  --repo Flutter-Global/olympus-app-of-apps \
  --title "feat(app-of-apps): [GSCP-XXXX] - Add <app-name> to <valuestream> clusters" \
  --body "$(cat <<'EOF'
## Summary

Registers `<app-name>` with the Olympus ArgoCD cluster(s) for the `<valuestream>` valuestream.

- Adds `<valuestream>-stg-argocd/app-of-apps/<app-name>.yml` — points ArgoCD at `<infra-repo>/argocd-apps/stg/`
- (Add prd entry here if included)

## Why

Without this registration, ArgoCD has no knowledge of the application and will never sync it to the cluster, regardless of what is in the infra repo.

## Post-merge

After merge, ArgoCD auto-syncs within ~1–2 minutes and creates the outer Application. No manual `kubectl apply` or `argocd app create` is needed.
EOF
)"
```

---

## Verification After Merge

Once the PR is merged, verify ArgoCD has picked up the new Application. Load the `olympus-get-argocd-credentials` and `olympus-argocd-cli` skills for authentication and CLI usage, then:

```bash
# List all Applications — your new one should appear
argocd app list | grep <app-name>

# Check its sync status
argocd app get <app-name>
```

A healthy outer Application will show `Synced` and `Healthy`. It will in turn create the inner Application(s) defined in `argocd-apps/<env>/` of the infra repo — those inner Applications are what actually deploy the Helm chart to the workload cluster.

If the Application does not appear after ~5 minutes, check:
1. The PR is merged to `main` (not a branch)
2. The file is in `<cluster>/app-of-apps/` — not directly in `<cluster>/`
3. The `metadata.name` is unique within the cluster directory

---

## Worked Example — apex-oncall-slack-bot

```
olympus-app-of-apps/
└── apex-stg-argocd/
    └── app-of-apps/
        └── apex-oncall-slack-bot.yml
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: apex-oncall-slack-bot
  namespace: argocd
spec:
  destination:
    namespace: argocd
    name: in-cluster
  project: applications
  sources:
    - repoURL: https://github.com/Flutter-Global/apex-oncall-slack-bot-infra
      path: argocd-apps/stg
      targetRevision: main
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
```

---

**Maintained By**: Apex Team
