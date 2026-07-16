---
name: onboard-to-olympus
description: Use this skill to understand the Olympus platform and applications are deployed to Kubernetes via the Olympus GitOps Pipeline
---
# Olympus - Skills Reference

## What I do

Provides detailed commands and reference information for onboarding applications to Olympus. This file contains implementation details that support the high-level workflow in the `onboard-to-olympus` agent.

## When to use me

- When onboarding an application to the Olympus Platform
- When working on tasks involving the Olympus platform
- When the agent needs specific bash commands for workflow verification, org-config operations, or validation
- When troubleshooting common Olympus deployment issues

## Reference documentation available

- **`olympus-platform-context`** (from `olympus-gitops-context`) — General information on the Olympus platform
- **`innersource-codebase-governor-context`** (from `olympus-gitops-context`) — How GitHub repositories are governed via Codebase Governor
- **`olympus-helm-kustomize-context`** (from `olympus-gitops-context`) — How application Helm charts are pipelined through environments
- **olympus-template-helm-infra repository** — Source of truth for infrastructure file templates and structure

---

# Onboarding Commands and Reference

## Step 1: Verify Application Repository Workflow

### Find workflow files
```bash
find .github/workflows -name "*.yaml" -o -name "*.yml"
```

### Check for Helm chart publication
```bash
# Search for helm push commands
grep -r "helm push.*jfrog" .github/workflows/

# Extract the actual URL used
JFROG_URL=$(grep -o "oci://flutter\.jfrog\.io/[a-zA-Z0-9_-]*-helmoci-local" .github/workflows/*.yaml | head -1)
echo "Workflow uses: $JFROG_URL"

# Common pattern:
# helm push <package>.tgz oci://flutter.jfrog.io/<module>-helmoci-local
```

### Check for infrastructure notification
```bash
# Look for notify job and GitHub App usage
grep -A 10 "notify-infrastructure-repo\|trigger-infra" .github/workflows/*.yaml
grep "create-github-app-token" .github/workflows/*.yaml
grep "ORG_GS_GROUP_OLYMPUS_INFRA_SECRET" .github/workflows/*.yaml
```

### Extract environment variables
```bash
# Find key configuration
grep "CHART_NAME\|IMAGE_NAME\|INFRASTRUCTURE_REPO" .github/workflows/*.yaml
```

---

## Discover Available JFrog Helm Repositories

### Clone forge-store-tf and list available modules

**Clone repository (always fresh)**:
```bash
FORGE_STORE_PATH=$(mktemp -d)
gh repo clone Flutter-Global/forge-store-tf "$FORGE_STORE_PATH" --depth 1 --quiet
cd "$FORGE_STORE_PATH"
```

**List all modules with helmoci repositories**:
```bash
for dir in modules/*/; do
  module=$(basename "$dir")
  if [ -f "${dir}${module}-helmoci.tf" ] || [ -f "${dir}${module}-helmoci-local.tf" ]; then
    echo "${module}"
  fi
done | sort
```

**Output example**:
```
cpp
fsp
gbp
gcd
gl-data
gpcp
gpd
grt
gstsports
idp
innersource
template
toci
```

### Extract JFrog Helm repo URL from workflow

**Search for helm push commands**:
```bash
# In application repository
grep -o "oci://flutter\.jfrog\.io/[a-zA-Z0-9_-]*-helmoci-local" .github/workflows/*.yaml
```

**Example output**:
```
oci://flutter.jfrog.io/gpcp-helmoci-local
```

### Check if app repo is whitelisted

**For a specific module** (e.g., `gpcp`):
```bash
cd "$FORGE_STORE_PATH"
APP_REPO="ops-channel-wingman"
MODULE="gpcp"

if grep -q "\"Flutter-Global/$APP_REPO\"" "modules/$MODULE/main.tf"; then
  echo "✅ $APP_REPO is whitelisted for $MODULE"
else
  echo "❌ $APP_REPO is NOT whitelisted for $MODULE"
fi
```

### Show all repos with whitelist status

**For current app**:
```bash
cd "$FORGE_STORE_PATH"
APP_REPO=$(basename $(git -C <app-repo-path> rev-parse --show-toplevel))

echo "JFrog Helm Repositories - Whitelist Status:"
echo ""

for dir in modules/*/; do
  module=$(basename "$dir")
  if [ -f "${dir}${module}-helmoci.tf" ] || [ -f "${dir}${module}-helmoci-local.tf" ]; then
    repo_url="oci://flutter.jfrog.io/${module}-helmoci-local"
    
    if grep -q "\"Flutter-Global/$APP_REPO\"" "${dir}main.tf" 2>/dev/null; then
      status="✅ Whitelisted"
    else
      status="❌ NOT whitelisted"
    fi
    
    printf "  %-20s %-50s %s\n" "$module" "$repo_url" "$status"
  fi
done | sort
```

### Whitelist an app repo (create PR)

> ⚠️ **forge-store-tf is a cross-team repo owned by the Forge team. Stop and confirm with the user before creating PRs or performing any operation in this repo.**

To add a repository to an existing module's OIDC whitelist, load and follow the **`forge-store-jfrog-whitelist`** skill from the `olympus-gitops-context` package. That skill covers the full workflow: cloning `forge-store-tf`, creating the feature branch, editing `modules/<valuestream>/main.tf`, committing, pushing, raising the PR, and requesting Sparta approval via `#gp-plat-eng-support`.

If no module exists yet for the valuestream (i.e. `modules/<valuestream>/` is missing entirely), use the **`forge-store-new-module`** skill instead.

### forge-store-tf Terraform apply gate

After the whitelist PR is merged, the resulting Terraform plan requires manual approval for the `artifactory` environment by a member of `maintainers-cap-global-services-cloud-platform`. Without this approval, JFrog OIDC auth fails silently with 403 Forbidden. Confirm the apply has completed before triggering the first CI run.

### Common repository URLs

**Format**: `oci://flutter.jfrog.io/<module>-helmoci-local`

**Examples**:
- GPCP: `oci://flutter.jfrog.io/gpcp-helmoci-local`
- GBP: `oci://flutter.jfrog.io/gbp-helmoci-local`
- GST Sports: `oci://flutter.jfrog.io/gstsports-helmoci-local`
- Apex: Check if `apex` module exists in forge-store-tf
- Ops Channel: Check if `ops-channel` module exists in forge-store-tf

**Note**: Not all valuestreams have their own JFrog Helm repository. Teams may share repositories (e.g., ops-channel may use gpcp-helmoci-local).

---

## Step 2: Determine Infrastructure Repository Name

### Check if already defined
```bash
grep "INFRASTRUCTURE_REPO:" .github/workflows/*.yaml
```

### Infer from app repo name
```bash
# Pattern: <app-repo-name>-infra
basename $(git rev-parse --show-toplevel)
# Example: ops-channel-wingman → ops-channel-wingman-infra
```

---

## Step 3: Verify Application Repo org-config

### Find app repo config
```bash
# In org-config repository
cd /path/to/org-config
find codebases -name "<app-repo-name>.yml"
```

### Check required configuration
```bash
# Verify apps and secrets
yq '.apps[]' codebases/<capability>/<app-repo-name>.yml
yq '.org-secrets.actions[]' codebases/<capability>/<app-repo-name>.yml
```

### Expected output
```yaml
apps:
  - group-jira-app
  - fg-trufflehog

org-secrets:
  actions:
    - ORG_GS_GROUP_OLYMPUS_INFRA_SECRET
```

### Create PR to add missing configuration
```bash
cd /path/to/org-config
git checkout -b gscp-<ticket>-update-<app-repo>-config
# Edit the YAML file
git add codebases/<capability>/<app-repo-name>.yml
git commit -m "chore(org-config): [TICKET] - Add Olympus secrets to <app-repo>"
git push origin gscp-<ticket>-update-<app-repo>-config
gh pr create --title "chore(org-config): [TICKET] - Add Olympus secrets to <app-repo>" --body "Add ORG_GS_GROUP_OLYMPUS_INFRA_SECRET for Olympus deployment"
```

---

## Step 4: Create Infrastructure Repository Declaration

### Check if infra repo config exists
```bash
# In org-config repository
ls -la codebases/<capability>/<infra-repo-name>.yml
```

### Create org-config YAML with template directive

**File**: `codebases/<capability>/<infra-repo-name>.yml`

```yaml
description: <App Name> infrastructure repo for Olympus deployment
using-template: olympus-template-helm-infra
branch-protections:
  - patterns:
      - main
    parameters:
      force-push-restricted-to:
        teams:
          - maintainers-cap-<capability>
        apps: []
      pull-request-bypassers:
        teams:
          - maintainers-cap-<capability>
        apps: []
      required-reviews-count: 0
apps:
  - group-jira-app
  - fg-trufflehog

org-secrets:
  actions:
    - ORG_GS_GROUP_OLYMPUS_INFRA_SECRET
```

**CRITICAL**: Line 2 must contain `using-template: olympus-template-helm-infra` to automatically clone the complete infrastructure template with all workflows, directory structure, and files. For new app repositories, use `using-template: olympus-template-helm-app` instead.

### Create PR
```bash
cd /path/to/org-config
git checkout -b gscp-<ticket>-create-<infra-repo-name>
# Create YAML file
git add codebases/<capability>/<infra-repo-name>.yml
git commit -m "chore(org-config): [TICKET] - Add <infra-repo-name> repo config"
git push origin gscp-<ticket>-create-<infra-repo-name>
gh pr create --title "chore(org-config): [TICKET] - Add <infra-repo-name> repo config" --body "Creates repository config for Olympus infrastructure deployment using olympus-template-helm-infra template"
```

### Wait for repo creation
```bash
# Check PR status
gh pr checks <PR-NUMBER> --watch

# After merge, wait ~5 minutes then verify
gh repo view Flutter-Global/<infra-repo-name>
```

---

## Step 4b: Declare Runner Group Access

Runner group access is declared in org-config via the `runner-groups:` field in each repository's codebase YAML.

Load the **`forge-github-runners-context`** skill from `olympus-gitops-context` for naming conventions, discovery commands, and the full `runner-groups:` YAML format.

**Identify the correct runner group** for the valuestream:

```bash
# List all runner groups available in org-config
gh api repos/Flutter-Global/org-config/contents/runner-groups \
  --jq '.[].name'
```

Or search existing codebase YAMLs for a known repo in the same capability:

```bash
ORG_CONFIG_TMP=$(mktemp -d)
gh repo clone Flutter-Global/org-config "$ORG_CONFIG_TMP" --depth 1 --quiet
grep -r "runner-groups" "$ORG_CONFIG_TMP/codebases/<capability>/"
```

**App repo** (`$APP_REPO`): Add `runner-groups:` to `codebases/<capability>/<app-repo>.yml` in the **Step 4 org-config PR** (same file, same PR):

```yaml
runner-groups:
  - forge-arc-<valuestream>-prod-1
  - forge-arc-<valuestream>-prod-2
```

**Infra repo** (`$INFRA_REPO`): Add `runner-groups:` inline in the new `codebases/<capability>/<infra-repo>.yml` created in **Step 5**.

If jobs queue indefinitely with no error after the PR merges, temporarily change `runs-on:` to `ubuntu-latest` in the affected workflow as a workaround, then revert once CBG has processed the org-config change.

---

## Step 5: Infrastructure Repository Reference

### Clone infrastructure repo (created from template)
```bash
cd /path/to/workspace
gh repo clone Flutter-Global/<infra-repo-name>
cd <infra-repo-name>
```

### Expected directory structure (from olympus-template-helm-infra)

The template provides the following structure with placeholder "TLA" values to be customized:

```
argocd-apps/
├── stg/          # Staging outer Application
│   └── TLA-stg.yaml
└── prd/          # Production outer Application
    └── TLA-prd.yaml

build-me/
├── stg/
│   ├── TLA-stg.yml          # ArgoCD Application (nested)
│   ├── TLA-project.yml      # ArgoCD Project
│   └── kustomization.yaml   # Kustomize base
└── prd/
    ├── TLA-prd.yml
    ├── TLA-project.yml
    └── kustomization.yaml

environments/
├── stg/
│   ├── targetRevision.yaml    # JSON Patch for chart version
│   ├── imageVersion.yaml      # JSON Patch for image repository and tag
│   └── kustomization.yaml     # Applies patches
└── prd/
    ├── targetRevision.yaml
    ├── imageVersion.yaml
    └── kustomization.yaml

variants/
├── stg/
│   └── values/
│       └── values.yaml        # Helm values for staging
└── prd/
    └── values/
        └── values.yaml        # Helm values for production

.github/
└── workflows/
    ├── update-chart-and-image-workflow-dispatch.yaml  # Promotion workflow
    ├── create-deployment-on-push.yaml                 # GitHub Deployment creation
    └── on-deployment-status-update.yaml               # Auto-promotion trigger
```

**Note**: All file templates and workflows are provided by the template. Agent should customize placeholder values, not generate files from scratch.

**Template Repository**: For complete file contents and latest structure, see [olympus-template-helm-infra](https://github.com/Flutter-Global/olympus-template-helm-infra)

### Key customization points

When customizing the template, focus on:
1. Renaming files containing "TLA" placeholder
2. Replacing "TLA" text in YAML files with actual app name
3. Updating cluster destination names
4. Updating image repository paths (ECR vs GHCR)
5. Customizing Helm values in `variants/` directories

**OCI Helm `repoURL` must include the chart name.** In `build-me/<env>/<app>-<env>.yaml`, the ArgoCD Application source `repoURL` must be the full OCI path including the chart name: `oci://flutter.jfrog.io/<module>-helmoci/<chart-name>`. ArgoCD does not append the `chart:` field to the URL — omitting the chart name causes sync to fail.

**`targetRevision.yaml` must contain a `chart: <chart-name>` field.** The `update-chart-and-image-v2.yml` reusable workflow locates this file via `grep -lr "chart: <chart-name>"`. Without it, the chart version is never updated and `targetRevision` stays permanently at `0.0.0`. The template includes `chart: TLA` — replace it, do not remove it.

### Image Registry Paths

**ECR Pull-Through Cache** (Recommended):
```yaml
# Docker pushes to GHCR, Kubernetes pulls from ECR
image:
  repository: 863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/<repo>/<image>
  tag: 0.0.0
```

**GHCR Direct** (Alternative):
```yaml
image:
  repository: ghcr.io/flutter-global/<repo>/<image>
  tag: 0.0.0
```

**Why ECR Pull-Through Cache**:
- Faster pulls (stays within AWS network)
- Better reliability (AWS infrastructure)
- Same workflow (app still pushes to GHCR)
- ECR automatically mirrors GHCR images

---

## Validate Infrastructure Structure

### Test kustomize rendering

Before committing infrastructure files, validate that kustomize can successfully render the manifests:

```bash
# Navigate to infra repo
cd /path/to/<infra-repo-name>

# Test staging environment
kustomize build build-me/stg/

# Test production environment
kustomize build build-me/prd/

# Test any other environments (qa, dev, etc.)
kustomize build build-me/qa/
```

**Expected output**: Clean YAML manifests with no errors. The output should show:
- ArgoCD AppProject
- ArgoCD Application with patches applied

**Common errors and fixes**:

1. **Error**: `json: cannot unmarshal array into Go struct field Kustomization.components of type types.Component`
   - **Cause**: Component path in `kustomization.yaml` is incorrect
   - **Fix**: Ensure `components:` points to correct path (e.g., `../../environments/stg`)

2. **Error**: `no matches for Id ~G_v1_ConfigMap|~X|<name>`
   - **Cause**: Resource not found that patch is trying to modify
   - **Fix**: Verify resource exists in `resources:` list before applying patches

3. **Error**: `unable to find one or more patches`
   - **Cause**: Patch file path is wrong in `kustomization.yaml`
   - **Fix**: Check `patches[].path` points to existing file

4. **Error**: `trouble configuring builtin PatchJson6902Transformer with config`
   - **Cause**: JSON Patch syntax error in patch files
   - **Fix**: Validate JSON Patch format (must be array with `op`, `path`, `value`)

### Validate ArgoCD Application syntax

```bash
# Optional: Validate against ArgoCD CRDs if available
kubectl apply --dry-run=client -f <(kustomize build build-me/stg/)
```

---

## Step 7: Register Application in App-of-Apps

Load and follow the **`olympus-app-of-apps`** skill from the `olympus-gitops-context` package. That skill covers the full workflow: cloning the repo, understanding the directory structure and cluster naming conventions, creating the YAML registration files for staging and production, committing, pushing, raising the PR, and verifying the Application appears in ArgoCD after merge.

---

## Step 8: Test End-to-End Promotion Flow

### Trigger app repo workflow manually
```bash
cd /path/to/app-repo
gh workflow run <workflow-name>.yaml --ref main -f deploy_env=stg
```

### Watch workflow execution
```bash
# Get latest run ID
RUN_ID=$(gh run list --workflow=<workflow-name>.yaml --limit 1 --json databaseId --jq '.[0].databaseId')

# Watch execution
gh run watch $RUN_ID --exit-status

# Check logs if failed
gh run view $RUN_ID --log-failed
```

### Check infrastructure repo for PR
```bash
cd /path/to/infra-repo
gh pr list

# View PR details
gh pr view <PR-NUMBER>
```

### Merge infrastructure PR
```bash
gh pr merge <PR-NUMBER> --squash
```

### Check ArgoCD sync status
```bash
# Port-forward to ArgoCD (if needed)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Or use argocd CLI
argocd app get <app-name> --refresh

# Watch sync progress
argocd app sync <app-name> --watch
```

### Verify deployment
```bash
# Check pod status
kubectl get pods -n <app-namespace>

# Check application endpoint
kubectl get svc -n <app-namespace>
curl https://<domain>/health
```

---

## Common Issues

### Workflow fails with "401 Unauthorized" on JFrog
- Verify JFrog OIDC configuration in workflow
- Check `jfrog/setup-jfrog-cli@v4` action configuration
- Confirm repository is whitelisted in `forge-store-tf/modules/<valuestream>/main.tf`

### Infrastructure repo not receiving notifications
- Verify `ORG_GS_GROUP_OLYMPUS_INFRA_SECRET` exists in app repo secrets
- Check GitHub App token generation step in workflow
- Verify infrastructure repo name matches workflow env variable

### ArgoCD sync fails
- Check ArgoCD Application manifest syntax with `kustomize build`
- Verify Helm chart exists in JFrog registry
- Check destination cluster name is correct
- Verify namespace exists or CreateNamespace=true is set

### Promotion PR not created
- Check ArgoCD notification configuration
- Verify `env` and `nextenv` labels on Application
- Check GitHub Deployment was created on PR merge
- Verify application reached "Healthy" status (required for notification trigger)
- Check `create-deployment-on-push.yaml` workflow ran successfully

### Template files not appearing in new repo
- Verify `using-template: olympus-template-helm-infra` is on line 2 of org-config YAML
- Check org-config PR was merged successfully
- Wait 5-10 minutes for Codebase Governor to process
- Check repository creation logs if available

### Kustomize build fails after customization
- Validate all file references in `kustomization.yaml` files
- Check that renamed files match references in kustomization
- Ensure labelSelector values match Application labels
- Run `kustomize build` locally before committing
