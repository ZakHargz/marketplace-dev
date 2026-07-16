# Adding a New Environment

To add a new environment to an existing Helm-pattern infra repo, create the four artefacts below, then apply the outer Application to the appropriate ArgoCD cluster.

## 1. Variant values (`variants/qa/values/values.yaml`)

```yaml
replicaCount: 1
resources:
  limits:
    cpu: 500m
    memory: 512Mi
ingress:
  hosts:
    - host: tennis-ui-bff-qa.flutter.io
```

## 2. Environment patches (`environments/qa/`)

```yaml
# kustomization.yml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
patches:
  - path: targetRevision.yaml
    target:
      kind: Application
      labelSelector: name=tennis-ui-bff-qa
  - path: imageTag.yaml
    target:
      kind: Application
      labelSelector: name=tennis-ui-bff-qa
```

```yaml
# targetRevision.yaml
- op: replace
  path: /spec/sources/0/targetRevision
  value: 0.1.0
```

```yaml
# imageTag.yaml
- op: replace
  path: /spec/sources/0/helm/valuesObject/image
  value:
    repository: 863507091340.dkr.ecr.eu-west-1.amazonaws.com/...
    tag: 0.1.0
```

## 3. Build-me composition (`build-me/qa/`)

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  namespace: tennis-ui-bff-qa
resources:
  - argo-application.yaml
  - argo-project.yaml
components:
  - ../../environments/qa
```

```yaml
# argo-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tennis-ui-bff-helm-qa
  labels:
    env: "qa"
    nextenv: "stg"  # Promotes to staging
    name: tennis-ui-bff-qa
spec:
  project: tennis-ui-bff-qa
  destination:
    name: gst-qa-euw1-app-1
    namespace: tennis-ui-bff-qa
  sources:
    - repoURL: oci://flutter.jfrog.io/.../tennis-ui-bff
      chart: tennis-ui-bff
      targetRevision: 0.0.0  # Patched by environments/
      helm:
        valuesObject:
          image:
            tag: 0.0.0  # Patched by environments/
        valueFiles:
          - $variants/variants/qa/values/values.yaml
    - repoURL: https://github.com/Flutter-Global/tennis-ui-bff-infra
      targetRevision: main
      path: variants/qa/values
      ref: variants
```

## 4. Outer Application (`argocd-apps/dev/tennis-ui-bff-qa.yml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tennis-ui-bff-qa
  namespace: argocd
spec:
  project: applications
  destination:
    name: in-cluster
    namespace: tennis-ui-bff
  source:
    repoURL: https://github.com/Flutter-Global/tennis-ui-bff-infra
    targetRevision: main
    path: build-me/qa/
```

## 5. Apply to cluster

Apply the outer Application to the `<valuestream>-stg-argocd` cluster (QA and staging environments both live on the stg ArgoCD instance).
