---
name: innersource-codebase-governor-context
description: Context on Flutter-Global's InnerSource repository governance system (Codebase Governor) — how to declare and provision GitHub repositories via the org-config repo, including the required configuration for Olympus infra repos.
---



# InnerSource GitHub Repository Governance

**Audience**: AI assistants needing to understand Flutter-Global's repository governance model  
**Purpose**: Core concepts for how repositories are created at Flutter-Global  
**Last Updated**: 2026-04-15

---

## Overview

Flutter-Global uses a **GitOps-style governance model** for managing GitHub repositories. Instead of creating repositories directly via GitHub API, all repository configuration is declared in YAML files in the [`Flutter-Global/org-config`](https://github.com/Flutter-Global/org-config) repository.

**System Name**: Codebase Governor (CBG)

**Critical Constraint**: You **CANNOT** create repositories via GitHub API.

---

## Key Concepts

### Capabilities

A **capability** is a business-aligned team grouping that owns related repositories.

**Location**: `codebases/<capability-name>/` in org-config repo

**Examples**: `global-services-cloud-platform`, `sports-feeds-tennis`, `platform-management`

**Structure**:
```
codebases/
├── global-services-cloud-platform/
│   ├── _defaults.yml              # Defaults for all repos in this capability
│   ├── ops-channel-wingman.yml    # Individual repo config
│   └── ops-channel-wingman-infra.yml
```

### Repository Configuration

Each repository = one YAML file in capability directory

**Naming**: `<repo-name>.yml`

**Inheritance**: Individual configs inherit from `_defaults.yml`, can override specific settings

---

## Creating a New Repository

### Process

1. User provides **capability name** (e.g., `global-services-cloud-platform`)
2. Create YAML file: `codebases/<capability>/<repo-name>.yml`
3. Commit and create PR in org-config repository
4. PR automatically validated by Codebase Governor
5. Capability maintainers auto-assigned as reviewers
6. PR merged → Repository created automatically (< 5 minutes)

### What You CANNOT Do

❌ Create repositories via GitHub API  
❌ Configure repository settings directly via API  
❌ Add secrets directly to repositories via API

### What You MUST Do

✅ Ask user for their capability name  
✅ Generate YAML config file content  
✅ Instruct user to create PR in org-config  
✅ Wait for user confirmation that PR is merged and repo exists

---

## Configuration Format

### Minimal Example (Inherits Defaults)

```yaml
description: Brief description of the repository
```

### Infrastructure Repository Example

```yaml
description: Infrastructure repo for my-application

apps:
  - group-jira-app      # Jira integration
  - fg-trufflehog       # Secret scanning

org-secrets:
  actions:
    - ORG_GS_GROUP_OLYMPUS_INFRA_SECRET  # Required for cross-repo workflows

branch-protections:
  - patterns:
      - main
    parameters:
      required-reviews-count: 0  # Override default for faster deployments
```

### Critical Fields

| Field | Purpose | Required for Olympus Infra |
|-------|---------|---------------------------|
| `description` | Repository description | Yes |
| `apps` | GitHub Apps to install | Recommended: `group-jira-app`, `fg-trufflehog` |
| `org-secrets.actions` | Expose org-level secrets | **CRITICAL**: Must include `ORG_GS_GROUP_OLYMPUS_INFRA_SECRET` |
| `branch-protections` | Override capability defaults | Optional (often set to 0 reviews for infra repos) |

---

## Critical for Olympus Infrastructure Repos

### Required Organization Secret

**MUST** include in `org-secrets.actions`:
```yaml
org-secrets:
  actions:
    - ORG_GS_GROUP_OLYMPUS_INFRA_SECRET
```

**Why**: This secret contains the private key for GitHub App (ID: 1078816), which enables:
- Application repo triggering infra repo workflows via `workflow_dispatch`
- Cross-repository communication in the deployment pipeline

**Without this**: Application repo cannot notify infrastructure repo of new artifacts → deployment pipeline breaks

### Recommended Apps

```yaml
apps:
  - group-jira-app      # Jira issue integration
  - fg-trufflehog       # Secret scanning
```

### Naming Convention

Pattern: `<app-name>-infra`

**Examples**:
- `ops-channel-wingman` → `ops-channel-wingman-infra`
- `apex-marketplace` → `apex-marketplace-infra`

---

## Automation Workflow

### Agent Workflow

When user requests repository creation:

1. **Detect app repo name** from current directory/repo
2. **Ask user**: "Which capability does this belong to?"
   - Provide examples if helpful
3. **Generate infra repo name**: `<app-name>-infra`
4. **Generate YAML content** with required fields
5. **Provide instructions**:
   ```
   Next Steps:
   1. Clone org-config: git clone https://github.com/Flutter-Global/org-config.git
   2. Create file: codebases/<capability>/<repo-name>-infra.yml
   3. Copy the YAML content below into the file
   4. Commit, push, create PR
   5. Wait for PR approval and merge (~5 minutes after merge)
   6. Return here once repository exists
   ```
6. **Wait for user confirmation**: "Repo is created"
7. **Proceed** with generating infra repo contents

### Finding Capability Name

**Method**: Ask the user directly

**Question**: "Which capability does this application belong to?"

User should know their capability or can search existing repos in org-config:
```bash
find codebases -name "*.yml" | grep <team-keyword>
```

---

## Capability Defaults Inheritance

### How It Works

Each capability has `_defaults.yml` with common settings:
- Branch protection rules
- Required reviewers
- Read/write access teams
- Default apps to install

Individual repository configs:
- Inherit these defaults automatically
- Can override any setting explicitly

### Example

**Capability Default** (`_defaults.yml`):
```yaml
defaults:
  delete-branch-on-merge: true
  branch-protections:
    - patterns:
        - main
      parameters:
        required-reviews-count: 1
```

**Individual Repo** (`my-infra-repo.yml`):
```yaml
description: My infrastructure repo
branch-protections:
  - patterns:
      - main
    parameters:
      required-reviews-count: 0  # Overrides default of 1
```

**Result**: Repo gets `delete-branch-on-merge: true` from defaults, but uses `required-reviews-count: 0`

---

## Further Reading

- **Codebase Governor Documentation**: https://developers.flutter.com/docs/cbg/
- **Repository Config Format**: https://developers.flutter.com/docs/repo-config/
- **Capability Defaults Format**: https://developers.flutter.com/docs/capability-defaults/

---

**Document Status**: Core reference for InnerSource governance  
**Maintained By**: GSCP Team
