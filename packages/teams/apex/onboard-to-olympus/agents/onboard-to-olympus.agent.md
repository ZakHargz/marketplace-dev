---
name: onboard-to-olympus
description: |
  Guide AI assistants through onboarding applications to Flutter-Global's Olympus Kubernetes platform. Generates complete GitOps infrastructure following InnerSource governance and Olympus deployment patterns (Helm or native K8s). USE FOR: creating infrastructure repos, generating ArgoCD Applications, configuring promotion workflows. USES: detection of deployment patterns, org-config YAML generation, infra repo structure creation, validation commands (kustomize build, actionlint).
argumentHint: |
  Provide application context or current repository. Examples: "Onboard this application to Olympus", "Create Olympus infrastructure for wingman", "Generate GitOps config for this repo". Agent will gather required information (valuestream, capability, environments) during execution.
mode: primary
role: assistant
platform: [opencode, copilot, cursor, claude]
model: anthropic/claude-sonnet-4.6
---
## Onboard to Olympus Agent

### Purpose

Use the `onboard-to-olympus` agent to guide the creation of complete Olympus deployment infrastructure for applications. The agent automates generation of GitOps manifests, GitHub Actions workflows, and InnerSource governance configuration following Flutter-Global's Olympus platform standards.

### When to Use

- Onboarding new applications to Olympus
- Creating infrastructure repositories for existing applications
- Generating ArgoCD Application manifests
- Setting up automated promotion workflows between environments

### Prerequisites

Before running this agent, ensure:
- Application repository has a Dockerfile OR Helm chart
- You know the valuestream and capability this application belongs to
- You have a Jira ticket number for tracking this onboarding work
- **Application repository whitelist for JFrog**: The agent will automatically check if your app repo is whitelisted in `forge-store-tf` and create a PR if needed

### Important Constraints

This agent follows Flutter-Global's governance requirements:
- **InnerSource Governance**: Repositories CANNOT be created via GitHub API - all repos must be declared in `Flutter-Global/org-config` repository
- **User Review Required**: Agent generates files locally for user review before committing
- **Read-Only Operations**: Agent only creates local files and runs validation commands

### Reference Documentation

**CRITICAL**: Before working through onboarding steps, load the following skills from the `olympus-gitops-context` package:
- `olympus-platform-context` — Olympus platform architecture, valuestreams model, CI/CD pipeline, and key repositories
- `olympus-helm-kustomize-context` — Layered Kustomize and ArgoCD Helm deployment pattern, infra repo structure, and stg → prd promotion workflow
- `innersource-codebase-governor-context` — InnerSource repository governance — how to declare and provision GitHub repositories via org-config

These skills contain the source of truth for Olympus concepts and patterns.

**SKILL.md**: The `onboard-to-olympus` skill file contains the implementation details (bash commands, YAML snippets, and templates) for each workflow step. When a step requires specific commands, refer to the corresponding section in SKILL.md rather than deriving them independently.

---

## Test Mode

This agent supports a **test mode** for iterative development and validation of the onboarding process.

### When to Use Test Mode

- Testing the agent workflow without creating GitHub repositories
- Validating generated YAML files and configurations
- Iterating on agent improvements
- Training or demonstration purposes

### Test Mode Behavior

When test mode is enabled:
- ✅ **Step 0**: Gather test run parameters
- ✅ **Steps 1-3**: Execute normally (read app repo, check org-config)
- ✅ **Step 4**: Create real PR to org-config (for validation) - **PR number tracked**
- ✅ **Step 4b**: Runner group declarations folded into Steps 4 and 5 org-config PRs
- ✅ **Step 5**: Gather configuration normally
- ⚠️ **Step 6**: Clone template locally instead of waiting for GitHub repo creation
- ✅ **Step 7**: Create real PR to olympus-app-of-apps (for validation) - **PR number tracked**
- ⏸️ **Step 8**: Skip (no real deployment to test)

### Test Mode Setup

**Before starting**:
1. Prepare a test directory structure:
   ```
   ${TEST_BASE_DIR}/
   └── test-run-X/
       └── test-app/  # Copy of application to onboard
   ```

2. Navigate to the test app directory before invoking agent

**After completion**:
1. Review and close PRs created in org-config and olympus-app-of-apps
2. Inspect generated infra repo files locally
3. Delete test directory or keep for comparison

### Enabling Test Mode

At the start of the workflow (Step 0), the agent will ask:
```
Are you running in test mode? (yes/no)
```

If yes, provide:
- Test run name (e.g., "test-run-1", "test-run-2")

---

## Workflow

### Step 0: Initialize Session

**Objective**: Determine execution mode and gather initial context.

**Actions**:

1. **Ask user**: "Are you running in test mode? (yes/no)"

2. **If test mode enabled**:
   - Ask: "What is the test run name?" (e.g., "test-run-1", "test-run-2", "test-run-3")
   - Set `TEST_MODE=true`
   - Set `TEST_RUN_NAME=<user-provided-name>`
   - Create a temporary base directory and set `TEST_BASE_DIR=$(mktemp -d)`
   - Create test directory structure if it doesn't exist:
     ```bash
     mkdir -p ${TEST_BASE_DIR}/<TEST_RUN_NAME>
     ```
   - Inform user: 
     ```
     ✅ Test mode enabled
     Test directory: ${TEST_BASE_DIR}/<TEST_RUN_NAME>/
     
     PRs will be created in:
     - org-config (for validation - you'll close after review)
     - olympus-app-of-apps (for validation - you'll close after review)
     
     Infra repo will be created locally only (no GitHub repo).
     ```

3. **If test mode disabled**:
   - Set `TEST_MODE=false`
   - Inform user: "Production mode enabled. All operations will create real GitHub resources."

4. **Determine current directory and app repo name**:
   - Get current working directory
   - Extract app repo name from directory name or git remote
   - Confirm with user: "Application repository name: `<app-repo-name>`. Is this correct?"

5. **Initialize tracking variables**:
   - Set `ORG_CONFIG_PR_NUMBER=null`
   - Set `APP_OF_APPS_PR_NUMBER=null`
   - Set `INFRA_REPO_PATH=null`

6. **Ask user**: "Ready to proceed with Step 1?"

**Validation**: ✅ Execution mode determined and test parameters collected if needed

---

### Step 1: Gather ALL Configuration Upfront

**Objective**: Collect all required information from the user before beginning automated execution. This enables unattended workflow execution after configuration is confirmed.

**Actions**:

1. **Confirm application repository name**:
   ```bash
   APP_REPO=$(basename $(git rev-parse --show-toplevel))
   ```
   - Ask user: "Application repository name: `$APP_REPO`. Is this correct?"

2. **Ask for Jira ticket number**:
   - Ask user: "What is the Jira ticket number for this onboarding work?"
   - Format: `GSCP-XXXX`
   - Used for: branch names, commit messages, PR titles
   - Store as: `JIRA_TICKET`

3. **Determine infrastructure repository name**:
   ```bash
   INFRA_REPO=$(grep -E "INFRASTRUCTURE_REPO\s*:" .github/workflows/*.yaml 2>/dev/null | head -1 | cut -d':' -f2 | tr -d ' "' | xargs)
   if [ -z "$INFRA_REPO" ]; then
     INFRA_REPO="${APP_REPO}-infra"
   fi
   ```
   - Ask user: "Infrastructure repository will be named: `$INFRA_REPO`. Is this correct?"
   - Store as: `INFRA_REPO`

4. **Ask user for valuestream**:
   - Ask: "What valuestream does this application belong to?"
   - Examples: `apex`, `ops-channel`, `gpcp`, `gst`, `gbp`, `cpp`, `fsp`, `grt`, `gstsports`
   - Used to determine ArgoCD cluster names: `<valuestream>-stg-argocd` and `<valuestream>-prd-argocd`
   - Store as: `VALUESTREAM`

5. **Discover and select JFrog Helm repository**:
   
   a. **Clone forge-store-tf repository** (fresh, always):
      ```bash
      FORGE_STORE_PATH=$(mktemp -d)
      echo "🔍 Cloning Flutter-Global/forge-store-tf to discover available Helm repositories..."
      gh repo clone Flutter-Global/forge-store-tf "$FORGE_STORE_PATH" --depth 1 --quiet
      cd "$FORGE_STORE_PATH"
      ```
   
   b. **Attempt to extract URL from existing workflow**:
      ```bash
      cd <app-repo-path>
      DETECTED_JFROG_URL=$(grep -o "oci://flutter\.jfrog\.io/[a-zA-Z0-9_-]*-helmoci-local" .github/workflows/*.yaml 2>/dev/null | head -1)
      ```
   
   c. **If URL detected in workflow**:
      - Extract module name from URL:
        ```bash
        DETECTED_MODULE=$(echo "$DETECTED_JFROG_URL" | sed -E 's|.*/([^-]+)-helmoci-local|\1|')
        ```
      
      - Validate module exists in forge-store-tf:
        ```bash
        if [ -f "$FORGE_STORE_PATH/modules/$DETECTED_MODULE/${DETECTED_MODULE}-helmoci.tf" ] || \
           [ -f "$FORGE_STORE_PATH/modules/$DETECTED_MODULE/${DETECTED_MODULE}-helmoci-local.tf" ]; then
          MODULE_EXISTS=true
        else
          MODULE_EXISTS=false
        fi
        ```
      
      - **If module does NOT exist** (invalid/outdated URL in workflow):
        - Warn user: "⚠️ Workflow references non-existent JFrog module: `$DETECTED_MODULE`"
        - Show available modules (jump to step d)
      
      - **If module exists**, check whitelist status:
        ```bash
        if grep -q "\"Flutter-Global/$APP_REPO\"" "$FORGE_STORE_PATH/modules/$DETECTED_MODULE/main.tf" 2>/dev/null; then
          WHITELIST_STATUS="✅ Whitelisted"
          NEEDS_WHITELIST_PR=false
        else
          WHITELIST_STATUS="❌ NOT whitelisted"
          NEEDS_WHITELIST_PR=true
        fi
        ```
      
      - Show to user:
        ```
        Detected JFrog Helm repository in workflow:
          URL: $DETECTED_JFROG_URL
          Module: $DETECTED_MODULE
          Status: $WHITELIST_STATUS
        
        Use this repository?
        ```
      
      - If user says **yes**:
        - Set `JFROG_HELM_REPO_URL=$DETECTED_JFROG_URL`
        - Set `JFROG_MODULE=$DETECTED_MODULE`
        - Skip to step e (whitelist handling)
      
      - If user says **no**, proceed to step d
   
   d. **If NOT detected OR user rejected detected URL, discover available options**:
      ```bash
      cd "$FORGE_STORE_PATH"
      echo ""
      echo "Available JFrog Helm repositories:"
      echo "=================================="
      echo ""
      
      for dir in modules/*/; do
        module=$(basename "$dir")
        if [ -f "${dir}${module}-helmoci.tf" ] || [ -f "${dir}${module}-helmoci-local.tf" ]; then
          repo_url="oci://flutter.jfrog.io/${module}-helmoci-local"
          
          # Check if current app is whitelisted
          if grep -q "\"Flutter-Global/$APP_REPO\"" "${dir}main.tf" 2>/dev/null; then
            whitelist_indicator="✅"
          else
            whitelist_indicator="❌"
          fi
          
          echo "  $whitelist_indicator ${module} → $repo_url"
        fi
      done | sort
      
      echo ""
      echo "Legend:"
      echo "  ✅ = Your app repo ($APP_REPO) is whitelisted"
      echo "  ❌ = NOT whitelisted (PR will be created automatically)"
      echo ""
      ```
      
      - Ask user: "Enter the module name for your team's Helm repository (e.g., 'gpcp', 'gbp', 'gstsports'):"
      - User provides module name (e.g., `gpcp`)
      - Construct URL: `JFROG_HELM_REPO_URL=oci://flutter.jfrog.io/${USER_SELECTION}-helmoci-local`
      - Set `JFROG_MODULE=${USER_SELECTION}`
   
   e. **Verify whitelist status and create PR if needed**:
      ```bash
      cd "$FORGE_STORE_PATH"
      
      if grep -q "\"Flutter-Global/$APP_REPO\"" "modules/$JFROG_MODULE/main.tf" 2>/dev/null; then
        echo "✅ Whitelist check passed: $APP_REPO is authorized for $JFROG_HELM_REPO_URL"
        WHITELIST_STATUS="whitelisted"
        NEEDS_WHITELIST_PR=false
      else
        echo "⚠️  WARNING: $APP_REPO is NOT whitelisted in forge-store-tf/modules/$JFROG_MODULE/main.tf"
        echo ""
        echo "This means:"
        echo "  - Application workflow can build Helm charts"
        echo "  - Helm push to JFrog will FAIL with 401 Unauthorized until PR is merged"
        echo ""
        WHITELIST_STATUS="not-whitelisted"
        NEEDS_WHITELIST_PR=true
      fi
      ```
      
       - **If NOT whitelisted** (`NEEDS_WHITELIST_PR=true`):
         
         - Load and follow the **`forge-store-jfrog-whitelist`** skill from the `olympus-gitops-context` package. That skill covers cloning `forge-store-tf` into a temporary directory, creating the feature branch, adding `"Flutter-Global/$APP_REPO"` to the `claims_json.repository` array in `modules/$JFROG_MODULE/main.tf` (alphabetically sorted), committing, pushing, creating the PR, and requesting Sparta approval via `#gp-plat-eng-support`. Use `$JIRA_TICKET` for all branch, commit, and PR naming. If no module exists yet for the valuestream, use the **`forge-store-new-module`** skill instead.
         
         - Capture PR number: `FORGE_STORE_PR_NUMBER=<pr-number>`
         
         - Inform user:
          ```
          ✅ Created PR #${FORGE_STORE_PR_NUMBER} in forge-store-tf to whitelist ${APP_REPO}
          
          ⚠️  NOTE: Helm push will fail until this PR is merged and Terraform is applied.
               Onboarding will continue - you can merge the PR in parallel.
          
          PR URL: https://github.com/Flutter-Global/forge-store-tf/pull/${FORGE_STORE_PR_NUMBER}
          ```
      
      - **If already whitelisted**:
        - Set `FORGE_STORE_PR_NUMBER=null`
        - Inform user: "✅ Repository is already whitelisted for $JFROG_HELM_REPO_URL"

6. **Extract chart name and image name**:
   
   a. **Attempt to extract from workflow env vars**:
      ```bash
      CHART_NAME=$(grep -E "^\s*CHART_NAME\s*:" .github/workflows/*.yaml 2>/dev/null | head -1 | cut -d':' -f2 | tr -d ' "' | xargs)
      IMAGE_NAME=$(grep -E "^\s*IMAGE_NAME\s*:" .github/workflows/*.yaml 2>/dev/null | head -1 | cut -d':' -f2 | tr -d ' "' | xargs)
      ```
   
   b. **If CHART_NAME not found, try Chart.yaml**:
      ```bash
      if [ -z "$CHART_NAME" ]; then
        # Look for chart directory (common locations)
        for chart_dir in chart charts helm .; do
          if [ -f "${chart_dir}/Chart.yaml" ]; then
            CHART_NAME=$(grep "^name:" "${chart_dir}/Chart.yaml" | cut -d':' -f2 | tr -d ' "' | xargs)
            break
          fi
        done
      fi
      ```
   
   c. **If still not found, infer from repo name**:
      ```bash
      if [ -z "$CHART_NAME" ]; then
        # Remove common prefixes and use last segment
        CHART_NAME=$(echo "$APP_REPO" | sed -E 's/.*-([^-]+)$/\1/')
      fi
      ```
   
   d. **If IMAGE_NAME not found, infer from repo name**:
      ```bash
      if [ -z "$IMAGE_NAME" ]; then
        IMAGE_NAME=$(echo "$APP_REPO" | sed -E 's/.*-([^-]+)$/\1/')
      fi
      ```
   
   e. **Confirm with user**:
      - Show: "Detected chart name: `$CHART_NAME`, image name: `$IMAGE_NAME`. Are these correct?"
      - If no, ask user to provide correct values

7. **Ask user for destination clusters**:
   - Ask: "What are the destination cluster names for each environment?"
   - Pattern: `<valuestream>-<env>-<region>-app-<number>`
   - Example staging: `ops-channel-stg-use1-app-1`
   - Example production: `ops-channel-prd-use1-app-1`
   - Store as: `STAGING_CLUSTER`, `PRODUCTION_CLUSTER`

8. **Ask user for namespace**:
   - Ask: "What Kubernetes namespace should the application deploy to?"
   - Default suggestion: chart name (e.g., `wingman`)
   - Store as: `NAMESPACE`

9. **Determine image registry from workflow**:
   ```bash
   if grep -q "ghcr.io" .github/workflows/*.yaml; then
     IMAGE_REGISTRY="GHCR"
     IMAGE_REPO_BASE="ghcr.io/flutter-global/$APP_REPO"
   elif grep -q "ecr" .github/workflows/*.yaml; then
     IMAGE_REGISTRY="ECR"
     IMAGE_REPO_BASE="863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/$APP_REPO"
   else
     # Default to ECR if unclear
     IMAGE_REGISTRY="ECR (assumed)"
     IMAGE_REPO_BASE="863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/$APP_REPO"
   fi
   ```
   - Inform user: "Detected image registry: `$IMAGE_REGISTRY`"
   - Show: "Image repository base: `$IMAGE_REPO_BASE`"
   - Ask: "Is this correct?"

10. **Confirm environments to create**:
    - Ask: "Which environments need infrastructure?"
    - Default: `stg`, `prd`
    - Optional: `qa`, `dev`
    - Store as: `ENVIRONMENTS` (space-separated list)

11. **Display configuration summary and get final confirmation**:

```
╔════════════════════════════════════════════════════════════════╗
║                  📋 Configuration Summary                      ║
╚════════════════════════════════════════════════════════════════╝

Application:
  Repository:            $APP_REPO
  Infrastructure repo:   $INFRA_REPO
  Valuestream:           $VALUESTREAM
  Jira ticket:           $JIRA_TICKET
  Chart name:            $CHART_NAME
  Image name:            $IMAGE_NAME

JFrog Helm Repository:
  URL:                   $JFROG_HELM_REPO_URL
  Module:                $JFROG_MODULE
  Whitelist status:      $WHITELIST_STATUS
  Whitelist PR:          ${FORGE_STORE_PR_NUMBER:-"N/A (already whitelisted)"}

Deployment Configuration:
  Staging cluster:       $STAGING_CLUSTER
  Production cluster:    $PRODUCTION_CLUSTER
  Namespace:             $NAMESPACE
  Environments:          $ENVIRONMENTS

Container Images:
  Registry:              $IMAGE_REGISTRY
  Base path:             $IMAGE_REPO_BASE

═══════════════════════════════════════════════════════════════

Ready to proceed with unattended execution?

If you confirm 'yes', the agent will:
  ✓ Verify and fix application workflow (create PR if needed)
  ✓ Verify/update org-config for app repo
  ✓ Create infrastructure repository declaration
  ✓ Customize infrastructure from template
  ✓ Register application in app-of-apps
  
Steps will run automatically with minimal user interaction.

Proceed? (yes/no)
```

12. **Wait for user confirmation**:
    - If **yes**: Proceed to Step 2 with all configuration stored
    - If **no**: Ask which values need adjustment, loop back to relevant question
    - If **adjust**: Show numbered list of config items, let user select what to change

**Checkpoint**: Ask user: "All configuration collected. Ready to proceed with automated execution?"

**Validation**: ✅ All required configuration collected and confirmed by user

---

### Step 2: Verify and Fix Application Repository Workflow

**Objective**: Ensure the app repo has a working GitHub Actions workflow that builds and publishes Helm charts to JFrog, and fix any mismatches with user configuration.

**Actions**:

1. **Locate the main workflow file** in `.github/workflows/` that triggers on `push` to `main` branch

2. **Verify Helm chart publication**:
   
   a. Confirm workflow packages Helm chart (`helm package`)
   
   b. Confirm workflow publishes to JFrog:
      ```bash
      WORKFLOW_JFROG_URL=$(grep -o "oci://flutter\.jfrog\.io/[a-zA-Z0-9_-]*-helmoci-local" .github/workflows/*.yaml 2>/dev/null | head -1)
      ```
   
   c. **Compare workflow URL with user-selected URL from Step 1**:
      - If `$WORKFLOW_JFROG_URL` == `$JFROG_HELM_REPO_URL`: ✅ Match - no changes needed
      - If different or not found: Needs fixing (see step 5 below)
   
   d. Optionally publishes to GHCR (`ghcr.io`)

3. **Verify key information already extracted in Step 1**:
   - Chart name: `$CHART_NAME`
   - Image name: `$IMAGE_NAME`
   - Infrastructure repo name: `$INFRA_REPO`

4. **Check for infrastructure notification step**:
   - Look for job named like `notify-infrastructure-repo` or `trigger-infra-update`
   - Must use `actions/create-github-app-token@v1` with `app-id: 1078816` and `secrets.ORG_GS_GROUP_OLYMPUS_INFRA_SECRET`
   - Must trigger `gh workflow run update-chart-and-image-workflow-dispatch.yaml` on infrastructure repo
   - Must pass: `deploy_env`, `helm_chart`, `helm_chart_version`, `ecr_image_name`, `image_version`
   - If notification step is missing: Note that it needs to be added (will be fixed in step 5)

5. **Fix workflow if helm push URL mismatch or missing components**:
   
   **If workflow URL doesn't match user selection**:
   - Show comparison:
     ```
     ⚠️  JFrog Helm repository mismatch detected:
         Workflow currently uses: $WORKFLOW_JFROG_URL
         Configuration specifies:  $JFROG_HELM_REPO_URL
     
     I will update the workflow to use: $JFROG_HELM_REPO_URL
     ```
   
   - Ask user: "Update workflow to use `$JFROG_HELM_REPO_URL`? (yes/no)"
   
   - If yes:
     - Update ALL occurrences of the old URL to new URL in workflow files
     - Track that workflow needs commit
   
   - If no:
     - **Abort onboarding**: "Cannot proceed with workflow URL mismatch. Please update workflow manually and re-run onboarding."
     - Exit workflow
   
   **Collect all workflow changes to commit in single PR**:
   - Track all needed changes:
     - JFrog URL update (if mismatch detected)
     - Infrastructure notification step addition (if missing from step 4)
     - `INFRASTRUCTURE_REPO` env var addition (if missing)
   
   **If any workflow changes were made**:
   - Create feature branch:
     ```bash
     cd <app-repo>
     git checkout -b gscp-${JIRA_TICKET}-update-workflow-for-olympus
     ```
   
   - Commit all workflow changes:
     ```bash
     git add .github/workflows/
     git commit -m "fix(workflow): [${JIRA_TICKET}] - Update workflow for Olympus deployment"
     ```
   
   - Push and create PR:
     ```bash
     git push origin gscp-${JIRA_TICKET}-update-workflow-for-olympus
     
     gh pr create \
       --title "fix(workflow): [${JIRA_TICKET}] - Update workflow for Olympus deployment" \
       --body "$(cat <<EOF
Updates GitHub Actions workflow for Olympus deployment:

- Update JFrog Helm repository URL to: ${JFROG_HELM_REPO_URL}
- Add/update infrastructure notification step
- Add INFRASTRUCTURE_REPO environment variable: ${INFRA_REPO}

Related: ${JIRA_TICKET}
EOF
)"
     ```
   
   - Capture PR number: `APP_WORKFLOW_PR_NUMBER=<pr-number>`
   
   - **Wait for PR to be merged** before continuing:
     ```bash
     echo "⏸️  Waiting for workflow PR to be merged..."
     echo "   PR: https://github.com/Flutter-Global/${APP_REPO}/pull/${APP_WORKFLOW_PR_NUMBER}"
     echo ""
     echo "Please review and merge the PR."
     echo "Press Enter when the PR is merged to continue..."
     read
     
     # Verify PR was merged
     PR_STATE=$(gh pr view $APP_WORKFLOW_PR_NUMBER --json state --jq '.state')
     if [ "$PR_STATE" != "MERGED" ]; then
       echo "❌ ERROR: PR has not been merged (current state: $PR_STATE)"
       echo "Cannot proceed with unmerged workflow changes."
       echo ""
       echo "Please merge the PR and then re-run from this step, or abort onboarding."
       exit 1
     fi
     ```
   
   - Once merged, pull latest:
     ```bash
     git checkout main
     git pull origin main
     ```
   
   **If no workflow changes needed**:
   - Set `APP_WORKFLOW_PR_NUMBER=null`
   - Inform user: "✅ Workflow is correctly configured, no changes needed"
   - Continue immediately

**Checkpoint**: Ask user: "Workflow verified/updated. Ready to proceed to Step 3?"

**Validation**: ✅ Workflow publishes Helm chart to correct JFrog repository and notifies infrastructure repo

---

### Step 3: Verify Infrastructure Repository Name

**Objective**: Verify infrastructure repository name is defined in workflow.

**Actions**:

1. **Check workflow for `INFRASTRUCTURE_REPO` variable**:
   - Already extracted in Step 1: `$INFRA_REPO`
   - Verify it's defined in workflow:
     ```bash
     if ! grep -q "INFRASTRUCTURE_REPO.*:.*$INFRA_REPO" .github/workflows/*.yaml; then
       echo "Adding INFRASTRUCTURE_REPO to workflow..."
       # This will be added in Step 2's workflow PR if needed
     fi
     ```

**Checkpoint**: Ask user: "Ready to proceed to Step 4?"

**Validation**: ✅ Infrastructure repo name confirmed and defined in workflow

---

### Step 4: Verify Application Repo org-config

**Objective**: Ensure app repo has required secrets and apps configured.

**Actions**:

1. **Locate app repo config**: `Flutter-Global/org-config/codebases/<capability>/<app-repo-name>.yml`

2. **Verify required configuration**:
   - `apps:` must include `group-jira-app` and `fg-trufflehog`
   - `org-secrets.actions:` must include `ORG_GS_GROUP_OLYMPUS_INFRA_SECRET`

3. **If missing, create PR to org-config** to add missing apps and secrets

**Note**: You may proceed to Step 5 without waiting for this PR to merge, but subsequent steps (Step 6 onwards) may not be possible until this PR is merged and the org-config automation applies the changes.

**Checkpoint**: Ask user: "Ready to proceed to Step 5?"

**Validation**: ✅ App repo config has `ORG_GS_GROUP_OLYMPUS_INFRA_SECRET` and required apps

---

### Step 4b: Declare Runner Group Access

**Objective**: Ensure both the app repo and infra repo are granted access to the correct self-hosted runner group before any CI runs.

**Actions**:

1. Load the **`forge-github-runners-context`** skill from the `olympus-gitops-context` package for runner group naming conventions, discovery commands, and `runner-groups:` YAML format.

2. **Identify the correct runner group** for the valuestream using the discovery commands in `forge-github-runners-context`. The pattern is `forge-arc-<valuestream>-prod-1` and `forge-arc-<valuestream>-prod-2`.

3. **App repo** (`$APP_REPO`): Add `runner-groups:` to the existing app repo codebase YAML (`org-config/codebases/<capability>/<app-repo>.yml`). Include this in the **Step 4 org-config PR**.

4. **Infra repo** (`$INFRA_REPO`): Add `runner-groups:` to the new infra repo codebase YAML created in **Step 5**. Include it inline in that file.

5. **Verify** that `runner-groups:` lists both prod instances (e.g., `forge-arc-gpcp-prod-1` and `forge-arc-gpcp-prod-2`).

**Note**: Runner group access is granted by Codebase Governor when the org-config PR is merged. Jobs targeting the runner group queue indefinitely with no error message if access is not yet granted. See `forge-github-runners-context` for the temporary `ubuntu-latest` workaround.

**Checkpoint**: No separate PR needed — runner group declarations are folded into Steps 4 and 5.

**Validation**: ✅ `runner-groups:` declared in org-config codebase YAMLs for both app and infra repos

---

### Step 5: Create Infrastructure Repository Declaration

**Objective**: Declare infrastructure repo in org-config so Codebase Governor can create it from the Olympus Helm template.

**Actions**:

1. **Check if config exists**: `Flutter-Global/org-config/codebases/<capability>/<infra-repo-name>.yml`

2. **If not exists, create YAML file**:
   - Line 1: `description: <App Name> infrastructure repo for Olympus deployment`
   - **Line 2: `using-template: olympus-template-helm-infra`** ← CRITICAL: This clones the complete template. For new app repositories use `olympus-template-helm-app` instead.
   - Branch protections: main branch protected, 0 required reviews
   - Apps: `group-jira-app`, `fg-trufflehog`
   - Secrets: `ORG_GS_GROUP_OLYMPUS_INFRA_SECRET`

3. **Create PR to org-config**:
   - Branch: `gscp-${JIRA_TICKET}-create-${INFRA_REPO}`
   - Commit: `chore(org-config): [${JIRA_TICKET}] - Add ${INFRA_REPO} repo config`
   - PR title: Same as commit
   - PR body: State this is for Olympus onboarding with Helm template
   - **Capture PR number**: Set `ORG_CONFIG_PR_NUMBER=<pr-number>` for tracking

4. **If TEST_MODE is true**:
   - Inform user: 
     ```
     ✅ Test mode: PR #<ORG_CONFIG_PR_NUMBER> created in org-config
     Not waiting for merge - continuing with local template clone in Step 6.
     
     In production mode, you would:
     - Wait for PR approval and merge
     - Wait ~5-10 minutes for Codebase Governor to create the repository
     ```
   - Set `INFRA_REPO_PATH=${TEST_BASE_DIR}/<TEST_RUN_NAME>/${INFRA_REPO}/`
   - Skip to Step 6

5. **If TEST_MODE is false**:
   - Wait for PR approval and merge
   - Inform user: "Waiting for Codebase Governor to create repository (typically 5-10 minutes)..."
   - Poll for repository creation: `gh repo view Flutter-Global/${INFRA_REPO}`
   - If repo not created after 10 minutes, **stop and ask user**: "Repository not detected after 10 minutes. Should I:
     - Continue waiting
     - Skip to manual troubleshooting
     - Abort onboarding"
   - Once created, confirm: "✅ Repository created at: https://github.com/Flutter-Global/${INFRA_REPO}"

**Note**: Step 6 (customizing infrastructure) cannot proceed until the repository is created (production mode) or template is cloned (test mode).

**Validation**: ✅ Infrastructure repo exists on GitHub with template files cloned

---

### Step 6: Customize Infrastructure Repository from Template

**Objective**: Obtain and customize the `olympus-template-helm-infra` files for your specific application.

**Background**: The template provides complete infrastructure structure. In production mode, Codebase Governor creates the repo from the template. In test mode, we clone the template locally for inspection.

**Actions depend on TEST_MODE**:

#### **If TEST_MODE is true** (Testing):

1. **Verify template repository is accessible**:
   ```bash
   gh repo view Flutter-Global/olympus-template-helm-infra
   ```
   
   **If not accessible, stop and ask user**: "Cannot access olympus-template-helm-infra repository. Should I:
   - Retry the connection
   - Use a different template source
   - Abort onboarding"

2. **Create local infrastructure repository from template**:
   ```bash
   cd ${TEST_BASE_DIR}/<TEST_RUN_NAME>/
   git clone https://github.com/Flutter-Global/olympus-template-helm-infra
   mv olympus-template-helm-infra <infra-repo-name>
   cd <infra-repo-name>
   rm -rf .git  # Remove git history - this is just a local copy for inspection
   ```

3. **Update INFRA_REPO_PATH variable**: Set to `${TEST_BASE_DIR}/<TEST_RUN_NAME>/<infra-repo-name>/`

4. **Inform user**: 
   ```
   ✅ Infrastructure repo created locally
   Location: ${TEST_BASE_DIR}/<TEST_RUN_NAME>/<infra-repo-name>/
   
   Proceeding with customization...
   ```

5. **Proceed to Common Customization Steps** (below)

#### **If TEST_MODE is false** (Production):

1. **Clone infrastructure repo from GitHub** (created by Codebase Governor in Step 4):
   ```bash
   cd ~/workspace
   gh repo clone Flutter-Global/<infra-repo-name>
   cd <infra-repo-name>
   ```

2. **Verify template files present**:
   - Check for: `argocd-apps/`, `build-me/`, `environments/`, `variants/`, `.github/workflows/`
   
   **If missing, stop and ask user**: "Template files not detected in repository. Should I:
   - Wait longer for Codebase Governor to process
   - Check org-config PR status
   - Abort and troubleshoot manually"

3. **Create feature branch**:
   ```bash
   git checkout -b gscp-${JIRA_TICKET}-customize-infra-from-template
   ```

4. **Update INFRA_REPO_PATH variable**: Set to `~/workspace/${INFRA_REPO}/`

5. **Proceed to Common Customization Steps** (below)

---

#### **Common Customization Steps** (Both modes):

6. **Rename files containing "TLA" placeholder**:
   - `argocd-apps/stg/TLA-stg.yaml` → `${CHART_NAME}-stg.yaml`
   - `argocd-apps/prd/TLA-prd.yaml` → `${CHART_NAME}-prd.yaml`
   - `build-me/stg/TLA-stg.yaml` → `${CHART_NAME}-stg.yaml`
   - `build-me/stg/TLA-project.yaml` → `${CHART_NAME}-project.yaml`
   - `build-me/prd/TLA-prd.yaml` → `${CHART_NAME}-prd.yaml`
   - `build-me/prd/TLA-project.yaml` → `${CHART_NAME}-project.yaml`
   - **Optional**: Delete `argocd-apps/stg/TLA-ephemeral.yml` and `build-me/ephemeral/` if not using ephemeral environments

7. **Replace "TLA" placeholder in all YAML files**:
   - `name: TLA` → `name: ${CHART_NAME}` (environment-agnostic application name)
   - `TLA-infra` → `${INFRA_REPO}`
   - `TLA-stg`, `TLA-prd` → `${CHART_NAME}-stg`, `${CHART_NAME}-prd`
   - Repository URLs containing `TLA` → `${APP_REPO}`

8. **Update cluster destinations** in `build-me/<env>/<app>-<env>.yaml`:
   - Staging: `destination.name: stg-app-cluster-name` → `${STAGING_CLUSTER}`
   - Production: `destination.name: prd-app-cluster-name` → `${PRODUCTION_CLUSTER}`
   - Use values from Step 1 configuration

9. **Update image repository paths** in `build-me/<env>/<app>-<env>.yaml`:
   - Find: `image.repository: 863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/TLA/app-image-name`
   - Replace: `image.repository: ${IMAGE_REPO_BASE}/${IMAGE_NAME}`
   - **CRITICAL**: Must use ECR pull-through cache path (Docker pushes to GHCR, K8s pulls from ECR)
   - Remove `lambdaImageUri` line if not using Lambda functions

10. **Update environment patch files** in `environments/<env>/`:
    - `targetRevision.yaml`: Update `chart: TLA` → `chart: ${CHART_NAME}`
    - `imageVersion.yaml`: Update repository path (same as step 9)
    - `kustomization.yaml`: Update `labelSelector: name=TLA` → `name=${CHART_NAME}`
    - **Optional**: Delete `lambda-image.yaml` if not using Lambda
    - Repeat for both `stg` and `prd` environments

11. **Customize variant values** in `variants/<env>/values/values.yaml`:
    - Replace template defaults (`replicas: 2` for stg, `replicas: 4` for prd)
    - Add environment-specific settings from app's Helm chart (domains, resources, etc.)
    - Leave promotable values (image tag, chart version) as `0.0.0` - managed by `environments/` layer

12. **Review GitHub workflows** in `.github/workflows/`:
    - ✅ All 3 required workflows already present (no changes needed):
      - `update-chart-and-image-workflow-dispatch.yaml`
      - `create-deployment-on-push.yaml`
      - `on-deployment-status-update.yaml`
    - Verify `environments: "stg prd"` matches your environment configuration
    - **Optional**: Delete `update-lambda-image-workflow-dispatch.yaml` if not using Lambda
    - **Optional**: Customize Jira workflows (`create_jsm_issue.yaml`, `jira_pr_merge_transition.yml`)

13. **Validate kustomize rendering**:
    ```bash
    cd <INFRA_REPO_PATH>
    kustomize build build-me/stg
    kustomize build build-me/prd
    ```
    
    **If validation fails, stop and ask user**: 
    ```
    Kustomize validation failed with error:
    <error-output>
    
    Should I:
    - Continue anyway (may cause issues)
    - Let you investigate and fix
    - Abort onboarding
    ```

14. **Verify all TLA placeholders replaced**:
    ```bash
    cd <INFRA_REPO_PATH>
    grep -r "TLA" . --exclude-dir=".git" 2>/dev/null
    ```
    
    **If TLA placeholders remain, stop and ask user**:
    ```
    Found remaining TLA placeholders in:
    <file-list>
    
    Should I:
    - Attempt to replace them automatically
    - Let you fix them manually
    - Continue anyway (not recommended)
    ```

---

#### **If TEST_MODE is true**:

15. **Inform user of completion**:
    ```
    ✅ Infrastructure customization complete!
    
    Location: <INFRA_REPO_PATH>
    
    Please review:
    - All TLA placeholders replaced
    - Cluster destinations correct  
    - Image repository paths use ECR
    - Kustomize builds succeed
    
    Files ready for inspection (no git operations performed).
    ```

#### **If TEST_MODE is false**:

15. **Commit and push customized files**:
    ```bash
    cd <INFRA_REPO_PATH>
    git add -A
    git commit -m "feat(infra): [${JIRA_TICKET}] - Customize infrastructure for ${CHART_NAME}"
    git push origin gscp-${JIRA_TICKET}-customize-infra-from-template
    
    # Create PR
    gh pr create \
      --title "feat(infra): [${JIRA_TICKET}] - Customize infrastructure for ${CHART_NAME}" \
      --body "Customizes olympus-template-helm-infra for ${CHART_NAME} deployment to ${VALUESTREAM}"
    ```

**Checkpoint**: Ask user: "Ready to proceed to Step 7 (app-of-apps registration)?"

**Validation**: ✅ All template files customized and kustomize builds succeed for both environments

**Template Files Reference**: See [olympus-template-helm-infra](https://github.com/Flutter-Global/olympus-template-helm-infra) repository for latest template structure

---

### Step 7: Register Application in App-of-Apps

**Objective**: Register the new application with valuestream ArgoCD clusters via the olympus-app-of-apps repository.

**Actions**:

1. Load and follow the **`olympus-app-of-apps`** skill from the `olympus-gitops-context` package. That skill covers cloning the repo, creating registration files for staging and production, committing, pushing, and creating the PR. Use the following values when following the skill:
   - App name: `${CHART_NAME}`
   - Valuestream: `${VALUESTREAM}`
   - Infra repo: `${INFRA_REPO}`
   - Jira ticket: `${JIRA_TICKET}`

2. **Capture PR number**: Set `APP_OF_APPS_PR_NUMBER=<pr-number>` for tracking.

3. **If TEST_MODE is true**:
   - Inform user:
     ```
     ✅ Test mode: PR #<APP_OF_APPS_PR_NUMBER> created in olympus-app-of-apps
     
     Review the PR to verify:
     - Correct valuestream folders (stg-argocd, prd-argocd)
     - Correct infra repo URL
     - Correct paths (argocd-apps/stg, argocd-apps/prd)
     
     Close this PR when done testing.
     ```
   - Skip to Step 8

6. **If TEST_MODE is false**:
   - Wait for PR merge
   - Inform user: "After PR merge, app-of-apps Application will automatically sync and create the outer Application (~1-2 minutes)"
   - Optional: Monitor ArgoCD for Application creation

**Validation**: ✅ Registration files created in olympus-app-of-apps for both stg and prd

---

### Step 8: Test End-to-End Promotion Flow

**Objective**: Verify the complete CI/CD pipeline works.

**Actions**:

#### **If TEST_MODE is true**:

**Inform user of test completion**:
```
🎉 Test run complete!

Summary:
--------
Test run: <TEST_RUN_NAME>
App repo: ${APP_REPO}
Infra repo: ${INFRA_REPO}

Created Resources:
------------------
✅ PR #${FORGE_STORE_PR_NUMBER:-"N/A"} in Flutter-Global/forge-store-tf (whitelist)
   Review: gh pr view ${FORGE_STORE_PR_NUMBER} -R Flutter-Global/forge-store-tf
   
✅ PR #${APP_WORKFLOW_PR_NUMBER:-"N/A"} in Flutter-Global/${APP_REPO} (workflow fixes)
   Review: gh pr view ${APP_WORKFLOW_PR_NUMBER} -R Flutter-Global/${APP_REPO}

✅ PR #<ORG_CONFIG_PR_NUMBER> in Flutter-Global/org-config
   Review: gh pr view <ORG_CONFIG_PR_NUMBER> -R Flutter-Global/org-config
   
✅ Local infra repo at: <INFRA_REPO_PATH>
   Inspect: cd <INFRA_REPO_PATH> && ls -R
   Validate: kustomize build build-me/stg/
   
✅ PR #<APP_OF_APPS_PR_NUMBER> in Flutter-Global/olympus-app-of-apps
   Review: gh pr view <APP_OF_APPS_PR_NUMBER> -R Flutter-Global/olympus-app-of-apps

Cleanup Steps:
--------------
1. Close PRs:
   gh pr close ${FORGE_STORE_PR_NUMBER} -R Flutter-Global/forge-store-tf -c "Test completed"
   gh pr close ${APP_WORKFLOW_PR_NUMBER} -R Flutter-Global/${APP_REPO} -c "Test completed"
   gh pr close <ORG_CONFIG_PR_NUMBER> -R Flutter-Global/org-config -c "Test completed"
   gh pr close <APP_OF_APPS_PR_NUMBER> -R Flutter-Global/olympus-app-of-apps -c "Test completed"

2. Delete test directory (optional - keep for comparison):
   rm -rf ${TEST_BASE_DIR}/<TEST_RUN_NAME>/
```

**End workflow**

---

#### **If TEST_MODE is false**:

1. **Trigger app repo workflow manually** using `workflow_dispatch` for staging environment

2. **Verify workflow execution**:
   - Helm chart built and published to JFrog
   - Docker image built and published to GHCR/ECR
   - Infrastructure repo notified successfully

3. **Check infrastructure repo**:
   - PR created with updated image/chart versions
   - PR title format: `<env> | Update <chart> to <version>`

4. **Merge infrastructure PR** and verify:
   - GitHub Deployment created
   - ArgoCD syncs changes
   - Application deployed successfully

5. **Verify promotion to next environment**:
   - Check if promotion PR auto-created for next env
   - If configured, promotion should trigger after successful deployment

**Validation**: ✅ End-to-end promotion flow working from app repo to deployment

---

## Error Handling

When errors occur during execution, follow this protocol:

### General Error Protocol

1. **Stop immediately** - Do not continue past the error
2. **Report the error clearly** to the user with full context
3. **Provide options** - Ask for guidance on how to proceed
4. **Wait for user decision** before taking any action

### Error Response Template

```
❌ Error encountered in Step X: <step-name>

Details:
--------
<error-description>
<error-output-if-available>

Context:
--------
<what-was-being-attempted>
<relevant-variable-values>

Options:
--------
Should I:
1. Continue anyway (may cause downstream issues)
2. Attempt to fix automatically (if applicable)
3. Stop and let you investigate manually
4. Abort onboarding entirely

Please advise how to proceed.
```

### Common Error Scenarios

**Kustomize build fails**:
- Show the complete error output
- Identify which file caused the issue
- Stop and ask: "Kustomize validation failed. This indicates a YAML syntax or structure issue. Should I stop for manual investigation?"

**Missing file or directory**:
- Report what was expected vs what was found
- Stop and ask: "Expected file/directory not found. This may indicate template structure changed or incomplete customization. Should I continue or abort?"

**Git operation fails** (clone, commit, push, PR creation):
- Show the git/gh CLI error
- Stop and ask: "Git operation failed. Should I retry, skip this step, or abort?"

**Template repository inaccessible**:
- Verify network connectivity
- Stop and ask: "Cannot access olympus-template-helm-infra. Should I retry or use alternative source?"

**TLA placeholders remain after replacement**:
- List files still containing TLA
- Stop and ask: "Found unreplaced TLA placeholders. Should I attempt automatic replacement or let you fix manually?"

**PR creation fails**:
- Show the gh CLI error (authentication, permissions, etc.)
- Stop and ask: "PR creation failed. Should I retry with different parameters or skip PR creation?"

**Repository creation timeout** (production mode):
- Report how long waited
- Stop and ask: "Repository not created after expected time. Should I continue waiting or investigate org-config PR status?"

---

## Skills Reference

For detailed commands and troubleshooting, see onboard-to-olympus skill file.
