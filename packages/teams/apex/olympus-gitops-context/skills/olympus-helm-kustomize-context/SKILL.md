---
name: olympus-helm-kustomize-context
description: This skill provides context on how Olympus uses a layered Kustomize architecture with ArgoCD to create a CI/CD pipeline for multi-environment Helm chart deployments.
---

# Helm Chart Kustomize Design for Multi-Environment Deployment

## Overview

Olympus deploys Helm-based applications using a layered Kustomize architecture with ArgoCD nested Applications. Concerns are split across four layers — **argocd-apps**, **build-me**, **variants**, and **environments** — enabling clean stg → prd promotion workflows. Helm charts are stored in an OCI registry (JFrog Artifactory); unlike the native Kubernetes pattern, rendered manifests are not stored in the infra repo.

## Directory Structure

```
<app-name>-infra/
├── argocd-apps/              # "Outer" ArgoCD Applications (one per env)
│   ├── dev/
│   │   └── <app>-qa.yml      # Points to build-me/qa/
│   ├── stg/
│   │   └── <app>-stg.yml     # Points to build-me/stg/
│   └── prd/
│       └── <app>-prd.yml     # Points to build-me/prd/
│
├── build-me/                 # Composition layer
│   ├── qa/
│   │   ├── kustomization.yaml
│   │   ├── argo-project.yaml
│   │   └── argo-application.yaml  # "Nested" Application (references Helm chart)
│   ├── stg/
│   │   ├── kustomization.yaml
│   │   ├── argo-project.yaml
│   │   └── argo-application.yaml
│   └── prd/
│       ├── kustomization.yaml
│       ├── argo-project.yaml
│       └── argo-application.yaml
│
├── variants/                 # Environment-locked configurations (cannot be promoted)
│   ├── qa/
│   │   ├── kustomization.yml
│   │   └── values/
│   │       └── values.yaml   # Env-specific Helm values (replicas, domains, resources)
│   ├── stg/
│   │   ├── kustomization.yml
│   │   └── values/
│   │       └── values.yaml
│   └── prd/
│       ├── kustomization.yml
│       └── values/
│           └── values.yaml
│
└── environments/             # Promotable configurations (can move stg → prd)
    ├── qa/
    │   ├── kustomization.yml
    │   ├── targetRevision.yaml  # Helm chart version (JSON Patch)
    │   └── imageTag.yaml        # Docker image tag (JSON Patch)
    ├── stg/
    │   ├── kustomization.yml
    │   ├── targetRevision.yaml
    │   └── imageTag.yaml
    └── prd/
        ├── kustomization.yml
        ├── targetRevision.yaml
        └── imageTag.yaml
```

## Layer Responsibilities

### 1. ArgoCD Apps Layer (`argocd-apps/<env>/`)

**Purpose**: "Outer" ArgoCD Applications that point to the build-me layer and are applied to the appropriate ArgoCD cluster.

**Key Characteristics**:

- One Application per environment
- Points to `build-me/<env>/` as the source path
- Deploys to `in-cluster` (the ArgoCD cluster itself, not the app cluster)
- Applied to different ArgoCD clusters based on environment:
  - `argocd-apps/qa/*.yaml` and `argocd-apps/stg/*.yaml` → Applied to `<valuestream>-stg-argocd`
  - `argocd-apps/prd/*.yaml` → Applied to `<valuestream>-prd-argocd`

**Example** (`argocd-apps/stg/<app>-stg.yml`):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tennis-ui-bff-stg
  namespace: argocd
spec:
  project: applications
  destination:
    name: in-cluster  # Deployed to the ArgoCD cluster
    namespace: tennis-ui-bff
  source:
    repoURL: https://github.com/Flutter-Global/tennis-ui-bff-infra
    targetRevision: main
    path: build-me/stg/  # Points to build-me layer
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
```

### 2. Build-Me Layer (`build-me/<env>/`)

**Purpose**: Composition layer that contains the "nested" ArgoCD Application and combines all configuration layers.

**Key Characteristics**:

- Contains the actual ArgoCD Application that references the Helm chart
- References ArgoCD Project definition
- Includes environment-specific components for patching
- This is where Kustomize combines base definitions with environment patches

**Contents**:

1. **`kustomization.yaml`** - Composes resources and components
2. **`argo-project.yaml`** - ArgoCD Project (namespace + RBAC boundaries)
3. **`argo-application.yaml`** - Nested Application with placeholder values

**Example** (`build-me/stg/kustomization.yaml`):

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  namespace: tennis-ui-bff-stg
resources:
  - argo-application.yaml  # The nested Application
  - argo-project.yaml
components:
  - ../../environments/stg  # Promotable patches (versions, tags)
```

**Example** (`build-me/stg/argo-application.yaml`):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tennis-ui-bff-helm-stg
  namespace: argocd
  annotations:
    notifications.argoproj.io/subscribe.on-helm-sync-succeeded.github: ""
  labels:
    env: "stg"          # Current environment
    nextenv: "prd"      # Next environment in promotion chain
    name: tennis-ui-bff-stg  # Used by Kustomize patch selectors
spec:
  project: tennis-ui-bff-stg
  destination:
    name: gst-stg-euw1-app-1  # Target application cluster
    namespace: tennis-ui-bff-stg
  sources:
    - repoURL: oci://flutter.jfrog.io/gstsports-helmoci/tennis-ui-bff
      chart: tennis-ui-bff
      targetRevision: 0.0.0  # PLACEHOLDER - patched by environments/
      helm:
        valuesObject:
          image:
            repository: 863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/tennis-ui-bff/tennis-ui-bff
            tag: 0.0.0  # PLACEHOLDER - patched by environments/
        valueFiles:
          - $variants/variants/stg/values/values.yaml  # References variants source
    - repoURL: https://github.com/Flutter-Global/tennis-ui-bff-infra
      targetRevision: main
      path: variants/stg/values
      ref: variants  # Named reference for valueFiles
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
    syncOptions:
      - CreateNamespace=true
```

**Key Points**:

- Uses **multi-source** feature (`sources:` array instead of `source:`)
- First source: OCI Helm chart with placeholder versions
- Second source: Infra repo for variant values files
- Labels drive the promotion chain (`env`, `nextenv`, `name`)
- Notification annotation: `on-helm-sync-succeeded` (Helm-specific)

### 3. Variants Layer (`variants/<env>/`)

**Purpose**: Contains **environment-locked** configurations that must never be promoted between environments.

**Key Characteristics**:

- Uses Kustomize Component (`kind: Component`)
- Contains Helm values files specific to each environment
- Values here are **permanently tied** to a specific environment
- Referenced by the nested Application's `valueFiles` directive

**Variables Managed**:

- Replica counts (e.g., `replicaCount: 3` in prod, `1` in staging)
- Resource limits (CPU, memory)
- Ingress domains (environment-specific URLs)
- Environment-specific feature flags
- AWS region-specific settings
- Database connection strings (per environment)

**Example** (`variants/stg/values/values.yaml`):

```yaml
replicaCount: 1

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

ingress:
  enabled: true
  hosts:
    - host: tennis-ui-bff-stg.flutter.io
      paths:
        - path: /
          pathType: Prefix

environment:
  name: stg
  aws_region: eu-west-1
```

**Example** (`variants/prd/values/values.yaml`):

```yaml
replicaCount: 3

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 1000m
    memory: 1Gi

ingress:
  enabled: true
  hosts:
    - host: tennis-ui-bff.flutter.io
      paths:
        - path: /
          pathType: Prefix

environment:
  name: prd
  aws_region: eu-west-1
```

### 4. Environments Layer (`environments/<env>/`)

**Purpose**: Contains **promotable** configurations that can move through the deployment pipeline using JSON Patch operations.

**Key Characteristics**:

- Uses Kustomize Component (`kind: Component`)
- Contains JSON Patch files that update placeholder values
- Values here can be **safely promoted** from stg → prd
- Updated automatically by GitHub Actions workflows

**Variables Managed**:

- Helm chart version (`targetRevision`)
- Docker image tag (`image.tag`)
- Any artifact versions that should be tested before production

**Example** (`environments/stg/kustomization.yml`):

```yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

patches:
  - path: targetRevision.yaml
    target:
      kind: Application
      labelSelector: name=tennis-ui-bff-stg
  
  - path: imageTag.yaml
    target:
      kind: Application
      labelSelector: name=tennis-ui-bff-stg
```

**Example** (`environments/stg/targetRevision.yaml`):

```yaml
- op: replace
  path: /spec/sources/0/targetRevision
  value: 0.13.0  # ACTUAL VERSION - updated by GitHub Actions
```

**Example** (`environments/stg/imageTag.yaml`):

```yaml
- op: replace
  path: /spec/sources/0/helm/valuesObject/image
  value:
    repository: 863507091340.dkr.ecr.eu-west-1.amazonaws.com/github/flutter-global/tennis-ui-bff/tennis-ui-bff
    tag: 0.98.0  # ACTUAL TAG - updated by GitHub Actions
```

**Key Mechanism**: The JSON Patch `op: replace` operation updates the placeholder `0.0.0` values in the nested Application with real version numbers.

## How the Layers Work Together

### Rendering Process

When Kustomize builds the final manifest:

1. **Build-me** provides the nested ArgoCD Application with placeholder values (`0.0.0`)
2. **Environments component** applies JSON Patches to replace placeholders with real versions
3. **Outer Application** (from `argocd-apps/`) points to the rendered build-me output
4. **ArgoCD** (in valuestream cluster) syncs the outer Application to `in-cluster`
5. **Nested Application** is created in ArgoCD, which then:
   - Fetches the Helm chart from OCI registry
   - Merges values from `variants/<env>/values/values.yaml`
   - Renders the final Helm templates
   - Deploys to the target application cluster

### ArgoCD Two-Cluster Architecture

**Critical Design**: Each valuestream has TWO separate ArgoCD instances:

1. **`<valuestream>-stg-argocd`** (e.g., `gst-stg-argocd`, `apex-stg-argocd`)
   - Manages ALL non-production environments: `qa`, `stg`, `dev`
   - Applications from `argocd-apps/qa/` and `argocd-apps/stg/` are applied HERE

2. **`<valuestream>-prd-argocd`** (e.g., `gst-prd-argocd`, `apex-prd-argocd`)
   - Manages ONLY production environment
   - Applications from `argocd-apps/prd/` are applied HERE

**Why Two Clusters**:

- Security isolation between production and non-production
- Separate RBAC and access controls
- Independent operational lifecycles
- Blast radius containment

## Promotion Workflow

### Complete Flow: Staging to Production

#### Phase 1: Initial Deployment to Staging

1. **Developer merges PR to main** in app repo
2. **GitHub Actions builds**:
   - Docker image → tagged with semver (e.g., `0.98.0`)
   - Helm chart → packaged and versioned (e.g., `0.13.0`)
   - Both pushed to respective registries (ECR + JFrog)
3. **App repo triggers infra repo** via `gh workflow run` using GitHub App
4. **Infra repo workflow** receives:
   - `deploy_env: "stg"`
   - `image_version: "0.98.0"`
   - `helm_chart_version: "0.13.0"`
5. **Reusable workflow updates** `environments/stg/` patch files:
   - `imageTag.yaml` → `tag: 0.98.0`
   - `targetRevision.yaml` → `value: 0.13.0`
6. **Creates PR** with title: `stg | Deploy image 0.98.0 and chart 0.13.0`
7. **Team reviews and merges PR**

#### Phase 2: GitHub Deployment Object Creation

8. **PR merged to main** triggers `create-deployment-on-push.yml`
9. **Workflow parses PR title** to extract environment: `stg | <description>` → env = "stg"
10. **Creates GitHub Deployment object** for commit SHA + environment

#### Phase 3: ArgoCD Sync to Staging

11. **ArgoCD (in stg cluster) detects push** to `main` in infra repo
12. **Kustomize renders** final manifests:
    - Applies JSON Patches from `environments/stg/`
    - Replaces placeholder `0.0.0` with real versions
13. **ArgoCD syncs outer Application** to `in-cluster`
14. **Nested Application created**, which:
    - Fetches Helm chart `0.13.0` from OCI registry
    - Merges `variants/stg/values/values.yaml`
    - Renders Helm templates with image tag `0.98.0`
    - Deploys to staging app cluster (`gst-stg-euw1-app-1`)
15. **ArgoCD sends notification** on successful Helm sync to GitHub
    - Includes labels: `env: "stg"`, `nextenv: "prd"`, `name: tennis-ui-bff-stg`

#### Phase 4: Automatic Promotion PR Creation

16. **GitHub receives notification**, triggers `on-deployment-status-update.yaml`
17. **Workflow uses ArgoCD labels** to determine promotion:
    - Current: `env: "stg"`
    - Next: `nextenv: "prd"`
18. **Copies values** from `environments/stg/` to `environments/prd/`:
    - `imageTag.yaml`: tag `0.98.0`
    - `targetRevision.yaml`: version `0.13.0`
19. **Creates promotion PR**: `prd | Promote from stg: image 0.98.0 and chart 0.13.0`
20. **Team reviews and merges PR**

#### Phase 5: Production Deployment

21. **Promotion PR merged** → triggers `create-deployment-on-push.yml` (for prd)
22. **Creates GitHub Deployment** for prd environment
23. **ArgoCD (in prd cluster) syncs** to **production ArgoCD cluster** (`<valuestream>-prd-argocd`)
24. **Production deployed** to `gst-prd-euw1-app-1`
25. **No further promotion** because `nextenv: "prd"` (same as current env - stops chain)

### Promotion Labels System

**For non-final environments** (`build-me/stg/argo-application.yaml`):

```yaml
labels:
  env: "stg"       # Current environment
  nextenv: "prd"   # Next environment in promotion chain
  name: tennis-ui-bff-stg  # Used by Kustomize patch selectors
```

**For the final environment** (`build-me/prd/argo-application.yaml`):

```yaml
labels:
  env: "prd"
  nextenv: "prd"   # Same as current - stops promotion chain
  name: tennis-ui-bff-prd
```

### What Gets Promoted vs What Stays Locked

**Promoted** (from `environments/stg/` to `environments/prd/`):

- Helm chart versions (`targetRevision: 0.13.0`)
- Docker image tags (`tag: 0.98.0`)
- Feature flag states (if managed in environments/)
- Artifact versions that have been tested in staging

**NOT Promoted** (stays locked in `variants/<env>/`):

- Replica counts
- Resource limits (CPU, memory)
- Ingress domains
- Environment names
- AWS regions
- Database connection strings
- Environment-specific configuration

## Adding a New Environment

See [adding-new-environment.md](adding-new-environment.md) for step-by-step instructions and full YAML examples covering variant values, environment patches, build-me composition, and the outer ArgoCD Application.

## CI/CD Integration

### GitHub Workflows

**Workflow 1: `update-chart-and-image-workflow-dispatch.yaml`** (in infra repo)

- Triggered by app repo via `workflow_dispatch`
- Receives: `deploy_env`, `image_version`, `helm_chart_version`
- Updates `environments/<env>/imageTag.yaml` and `targetRevision.yaml`
- Creates PR for review

**Workflow 2: `create-deployment-on-push.yml`** (in infra repo)

- Triggered on PR merge to `main`
- Parses PR title to extract environment
- Creates GitHub Deployment object

**Workflow 3: `on-deployment-status-update.yaml`** (in infra repo)

- Triggered by ArgoCD notification (via `deployment_status` event)
- Reads ArgoCD Application labels (`env`, `nextenv`)
- Copies `environments/<current>/` to `environments/<next>/`
- Creates promotion PR

## Comparison: Helm Pattern vs Native Kubernetes Pattern

| Aspect                   | Native K8s Pattern                      | Helm Pattern                                   |
| ------------------------ | --------------------------------------- | ---------------------------------------------- |
| **ArgoCD Apps**          | Single Application                      | Nested Applications (outer + inner)            |
| **build-me/ contents**   | `kustomization.yml` only                | `kustomization.yaml` + nested Application YAML |
| **Source definition**    | Single `source:`                        | Multi-source `sources:` array                  |
| **Manifests location**   | `base/` directory in same repo          | External OCI registry + values in repo         |
| **Image tag updates**    | Kustomize patches                       | Helm `valuesObject` + JSON Patch               |
| **Values files**         | N/A                                     | `variants/<env>/values/values.yaml`            |
| **Notification**         | `on-app-sync-succeeded`                 | `on-helm-sync-succeeded`                       |
| **AppProject**           | Shared (e.g., "applications")           | Dedicated per app/env                          |
| **Package management**   | None (raw YAML)                         | Helm (versioned, templated charts)             |
| **Template engine**      | Kustomize only                          | Helm + Kustomize                               |
| **Version tracking**     | Git commit + image tag                  | Helm chart version + image tag                 |
| **Reusability**          | Copy/paste manifests                    | Helm chart reused across envs                  |
| **Complexity**           | Lower (fewer layers)                    | Higher (nested Apps, multi-source)             |
| **Best for**             | Simple apps, Crossplane Workspaces      | Complex apps, microservices, third-party apps  |
