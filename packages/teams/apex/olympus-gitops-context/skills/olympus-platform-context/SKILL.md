---
name: olympus-platform-context
description: High-level reference for the Olympus platform: its GitOps architecture on AWS EKS, the valuestreams model, ArgoCD-based CI/CD pipeline, and key repositories.
---

### What Olympus is

- Olympus is Flutter Group’s paved-road, GitOps-based platform for deploying and operating Kubernetes applications on AWS EKS.
    
- Built around ArgoCD for continuous delivery, with infrastructure and app state declared in GitHub and reconciled to clusters.
    
- Provides opinionated system apps, security guardrails, and automation to standardise multi-account, multi-region delivery.
    

### Core components

- Amazon EKS: Kubernetes control plane and worker nodes for application and ArgoCD clusters.
    
- ArgoCD: GitOps engine; syncs infra and workloads from Git to clusters; app-of-apps and ApplicationSets patterns are used.
    
- Crossplane: Kubernetes-native provisioning of AWS resources via compositions; integrates with GitOps flow.
    
- Kyverno: Policy enforcement and automation in clusters (e.g., secret propagation, Argo registration automation).
    
- Karpenter: Just-in-time autoscaling of worker nodes for cost/perf efficiency.
    
- Nginx Ingress: L7 ingress, TLS termination, routing.
    

### Valuestreams model

- A Valuestream is a business-aligned grouping that owns its delivery lanes and environments.
    
- Typical topology: two ArgoCD clusters per valuestream (`<valuestream>-stg-argocd` managing qa/dev/stg, and `<valuestream>-prd-argocd` managing prd) + one or more application EKS clusters per environment/region.
    
- Management clusters provision and register valuestream/app clusters; valuestream ArgoCD instances own deployment into their app clusters.
    

### GitOps and CI/CD at a glance

- Source of truth: GitHub repos declare desired state (apps and infra). All changes flow via Pull Requests to main (trunk-based).
    
- CI builds and publishes artifacts (containers/Helm). Workflows dispatch updates to the related infra/manifest repo (e.g., image tags/values).
    
- ArgoCD detects Git changes and syncs to the appropriate EKS cluster(s). Manual cluster changes are reverted to match Git.
    
- Environment promotion (stg → prd): after a successful sync in staging, ArgoCD Notifications triggers a GitHub repository_dispatch; a workflow (from shared actions) opens/updates a PR to promote config to production. Merging that PR causes ArgoCD to sync prod.
    

### Key GitHub repositories (names only)

- olympus-bootstrap — scripts/manifests to stand up management and valuestream clusters; wiring for ArgoCD and registration.
    
- olympus-management (template) — template structure for management/system apps configuration and cluster onboarding.
    
- olympus-system-apps-helm — Helm charts for platform system apps (ArgoCD, Kyverno, Karpenter, ingress, observability, etc.).
    
- olympus-grafana-alerts — System-level Grafana/Prometheus alert rules packaged and deployed to management clusters.
    
- gtt-github-actions — Reusable GitHub Actions/workflows (e.g., update-image-version, promote-image) used by Olympus pipelines.
    
- Per-application repos — “app repo” (source, CI, image build) and “infra/manifest repo” (Helm values/ArgoCD apps/ApplicationSets).
    

### CI/CD flow (brief)

1. Developer merges PR in the app repo; CI builds and publishes a new artifact version.
    
2. A workflow dispatch updates the infra/manifest repo to reference the new version (e.g., Helm values).
    
3. ArgoCD in the valuestream cluster detects the change and syncs to the staging application cluster.
    
4. On successful staging sync, ArgoCD Notifications sends a repository_dispatch to GitHub.
    
5. A shared workflow (from gtt-github-actions) raises/updates a PR to promote config to production; merge completes the promotion; ArgoCD syncs prod.
    

### App-of-Apps Registry

- Each valuestream ArgoCD cluster has a parent "app-of-apps" Application that watches a folder in the `olympus-app-of-apps` repository.
    
- To deploy a new application to a valuestream, add an ArgoCD Application YAML file to `olympus-app-of-apps/<valuestream>-<env>-argocd/app-of-apps/<app-name>.yml`.
    
- This registration file points to the application's infra repo at path `argocd-apps/<dev|prd>/`, creating the bridge between the app-of-apps pattern and the individual application's GitOps manifests.
    
- Pattern: app-of-apps watches repo → syncs registration files → each registration points to an infra repo → infra repo contains the actual deployment manifests.
    

### Glossary

- App repo: Source code repository; builds/publishes container or chart via CI.
    
- Infra/manifest repo: GitOps repo holding ArgoCD Applications/ApplicationSets and Helm values per env/cluster.
    
- App-of-apps: An ArgoCD pattern where a parent Application manages many child Applications from a folder/manifest set.
    

### How to talk about Olympus (prompting notes for AI)

- Emphasise Git as the single source of truth and ArgoCD reconciliation; avoid describing imperative kubectl changes.
    
- Use the valuestream framing: two ArgoCD instances per valuestream (one for staging/qa/dev, one for production), each deploying to that valuestream’s application clusters.
    
- Describe promotions as Git-driven (stg → prd) via ArgoCD Notifications + GitHub repository_dispatch + PRs.
    

