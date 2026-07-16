# onboard-to-olympus

Guides new team members through Olympus platform onboarding and setup

## Installation

```bash
apm install Flutter-Global/apex-marketplace/packages/teams/apex/onboard-to-olympus
```

## What's Included

This hybrid package provides both an **agent** and a **skill** for comprehensive Olympus onboarding support:

### Agent: `onboard-to-olympus`

An interactive AI agent that automates the end-to-end process of onboarding an application to the Olympus platform.

#### Example prompts

##### Simple

```text
Please onboard the <APP_NAME> in this project to the apex staging cluster.
The source code is in /src. Please create the GitHub workflows needed to
package the code into a Helm chart and publish to JFrog. Then complete
the rest of the onboarding process.
```

##### Medium

```text
Please onboard <APP_REPO_NAME> to the Olympus platform.

- Jira ticket:    GSCP-XXXX
- Valuestream:    apex
- Environments:   stg, prd

The app repo is Flutter-Global/<APP_REPO_NAME>.
```

##### Comprehensive

```text
Please onboard <APP_REPO_NAME> to the Olympus platform.

- Jira ticket:          GSCP-XXXX
- Valuestream:          <e.g. apex, gpcp, gbp>
- Capability:           <e.g. global-services-cloud-platform, sports-feed-tennis>
- Staging cluster:      <e.g. apex-stg-use1-app-1>
- Production cluster:   <e.g. apex-prd-use1-app-1>
- Namespace:            <e.g. my-app>
- JFrog Helm module:    <e.g. gpcp>
- Environments:         stg, prd

The app repo is Flutter-Global/<APP_REPO_NAME>.
The infra repo should be named <APP_REPO_NAME>-infra (or specify if different).
```

#### Test mode

To run a safe dry-run, append the following to any prompt above:

```text
This is a test run — test run name: <test-run-name>
```

The agent will create real PRs against `org-config` and `olympus-app-of-apps` for review. **Close these PRs — do not merge them** — or they will trigger real infrastructure changes.

#### Prompt Field Reference

- **Valuestream** — determines the ArgoCD cluster names (`<valuestream>-stg-argocd`, `<valuestream>-prd-argocd`) and the app-of-apps folders the agent will write to.
- **Capability** — the path segment used in `Flutter-Global/org-config` (e.g. `global-services-cloud-platform`, `sports-feed-tennis`). Typically matches the team or business domain. If unsure, search the `org-config` repo: `find codebases -name "*.yml" | grep <team-keyword>`.
- **JFrog Helm module** — the module name used in `forge-store-tf` (e.g. `gpcp`, `gbp`). The agent will check whether your repo is whitelisted and raise a PR if not.
- **Cluster names** — follow the pattern `<valuestream>-<env>-<region>-app-<n>`. If unsure, check the `olympus-app-of-apps` repo for examples from your valuestream.

## Features

- Verifies and fixes the app repo's GitHub Actions workflow before onboarding begins
- Checks whether the app repo is whitelisted in the JFrog Helm module and raises a PR to `forge-store-tf` if not
- Creates the infra repo declaration in `Flutter-Global/org-config` following Codebase Governor (CBG) standards
- Generates the infrastructure repo from template and customises it for the target valuestream and environments
- Registers the app in `olympus-app-of-apps` for both staging and production
- Confirms all configuration with you before making changes and pauses on anything unexpected
- Supports **test mode** for safe dry-runs without creating live repositories

## Version History

See [CHANGELOG.md](CHANGELOG.md)

## License

MIT - Internal use for Flutter-Global
