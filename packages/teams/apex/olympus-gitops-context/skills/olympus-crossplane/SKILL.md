---
name: olympus-crossplane
description: Knowledge of Olympus Crossplane infrastructure patterns. Use when writing Crossplane claims to provision AWS resources, debugging infrastructure provisioning failures, or understanding how XRDs and Compositions work in the Olympus platform.
---

# Olympus Crossplane

The `olympus-crossplane` repo (https://github.com/Flutter-Global/olympus-crossplane) is the Olympus platform's catalogue of Crossplane Compositions for provisioning AWS resources declaratively via Kubernetes claims. All claims use API group `olympus.crossplane/v1`.

## Finding Available XRDs

Compositions live in `charts/crossplane-compositions/templates/<service>/`. Each service directory contains a `definition.yml` (XRD) and `composition.yml`. Explore this directory to discover what is available (RDS Aurora, DynamoDB, S3, Lambda, IAM, ElastiCache, MSK, OpenSearch, Keyspaces, SQS, EKS, API Gateway, and more).

> **Source of truth**: Compositions in `templates/` are generated from `template-fragments/` via `scripts/build_compositions.sh`. When reading or debugging a composition, check `template-fragments/` if the `templates/` version appears incomplete or auto-generated.

## Compositions vs Workspaces

Two distinct patterns exist for Crossplane-provisioned infrastructure:

- **Compositions** (`olympus.crossplane/v1`): Kubernetes-native claim → composition → managed resources. Defined in the olympus-crossplane repo. Use for standard AWS resources.
- **Terraform Workspaces** (`Workspace.tf.upbound.io/v1beta1`): Embed Terraform HCL inline in `spec.forProvider.module`. Used for bespoke provisioning not covered by a composition.

When debugging a `Workspace` failure: the Terraform provider defaults to the pod's environment region if no explicit `provider "aws" { region = ... }` block is set — this causes "resource not found" errors when AWS resources are in a different region.

## Writing Claims

### `forProvider` — open schema

All XRDs expose `forProvider` with `x-kubernetes-preserve-unknown-fields: true`. Any field valid for the underlying Upbound AWS managed resource can be passed here (e.g. `region`, `engineVersion`, `backupRetentionPeriod`). Fields set in `forProvider` override composition defaults.

### `eksClusterName`

Most compositions require an `eksClusterName` field. This drives a lookup against an `EnvironmentConfig` named after the cluster, from which the composition resolves cluster-specific values (VPC ID, subnets, account ID, region). Use the exact cluster name (e.g. `apex-stg-use1-app-1`).

### Defaults to be aware of

| Field | Default | Override when... |
|---|---|---|
| `resourceConfig.deletionPolicy` | `Orphan` | Set to `Delete` for non-prod to enable clean teardown |
| `resourceConfig.providerConfigName` | `aws-provider` | Non-default provider config only |

## ArgoCD + Crossplane

- An ArgoCD Application showing **Synced** means only that the claim YAML was applied — not that the underlying AWS resource has been provisioned. Inspect the composite resource status directly.
- A failing `Workspace.tf.upbound.io` affects only AWS infrastructure provisioning; existing Kubernetes pods continue running unaffected.

## Related Skills

- **`olympus-helm-kustomize-context`** — the `base/variants/build-me/argocd-apps` pattern used in consuming repos when deploying Crossplane claims
- **`olympus-platform-context`** — overall Olympus GitOps architecture; situates Crossplane within the broader platform
- **`olympus-argocd-cli`** — inspecting and troubleshooting ArgoCD Applications that manage Crossplane claims
- **`olympus-kubeconfig-context-selection`** — required for `kubectl get xrd`, `kubectl describe composite`, and other discovery commands
- **`get-aws-credentials`** — required when verifying that provisioned AWS resources exist in AWS
