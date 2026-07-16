---
name: confluence
description: Use confluence-cli to read, search, create, update, move, delete, and convert Confluence pages and attachments from the terminal.
---

# confluence-cli Skill

A CLI tool for Atlassian Confluence. Lets you read, search, create, update, move, delete, and convert pages and attachments from the terminal or from an agent.

## Installation

```sh
npm install -g confluence-cli
confluence --version   # verify install
```

## Configuration

**Preferred for agents — environment variables (no interactive prompt):**

| Variable | Description | Example |
|---|---|---|
| `CONFLUENCE_DOMAIN` | Your Confluence hostname | `company.atlassian.net` |
| `CONFLUENCE_API_PATH` | REST API base path | `/wiki/rest/api` (Cloud) or `/rest/api` (Server/DC) |
| `CONFLUENCE_AUTH_TYPE` | `basic` or `bearer` | `basic` |
| `CONFLUENCE_EMAIL` | Email address (basic auth only) | `user@company.com` |
| `CONFLUENCE_API_TOKEN` | API token or personal access token | `ATATT3x...` |
| `CONFLUENCE_PROFILE` | Named profile to use (optional) | `staging` |
| `CONFLUENCE_READ_ONLY` | Block all write operations when `true` | `true` |
| `CONFLUENCE_FORCE_CLOUD` | Force Cloud link format for custom domains | `true` |
| `CONFLUENCE_LINK_STYLE` | Override link rendering: `smart`, `plain`, or `wiki` | `plain` |

**Global `--profile` flag (use a named profile for any command):**

```sh
confluence --profile <name> <command>
```

Config resolution works in two stages:
- **Direct env config:** If both `CONFLUENCE_DOMAIN` and `CONFLUENCE_API_TOKEN` are set, they are used directly and the config file / profiles are not consulted.
- **Profile-based config:** Otherwise, a profile is selected in this order: `--profile` flag > `CONFLUENCE_PROFILE` env > `activeProfile` in config > `default`.

**Non-interactive init (good for CI/CD scripts):**

```sh
confluence init \
  --domain "company.atlassian.net" \
  --api-path "/wiki/rest/api" \
  --auth-type basic \
  --email "user@company.com" \
  --token "ATATT3x..."
```

**Cloud vs Server/DC:**
- Atlassian Cloud (`*.atlassian.net`): use `--api-path "/wiki/rest/api"`, auth type `basic` with email + API token
- Atlassian Cloud (custom domain): if your Cloud instance uses a custom domain (e.g., `wiki.example.org`), set `CONFLUENCE_FORCE_CLOUD=true` or add `"forceCloud": true` to your profile in `~/.confluence-cli/config.json`. Without this, links will render incorrectly.
- Atlassian Cloud (scoped token): use `--domain "api.atlassian.com"`, `--api-path "/ex/confluence/<your-cloud-id>/wiki/rest/api"`, auth type `basic` with email + scoped token. Get your Cloud ID from `https://<your-site>.atlassian.net/_edge/tenant_info`. Recommended for agents (least privilege).
- Self-hosted / Data Center: use `--api-path "/rest/api"`, auth type `bearer` with a personal access token (no email needed)

**Scoped API token for agents (recommended):**

```sh
export CONFLUENCE_DOMAIN="api.atlassian.com"
export CONFLUENCE_API_PATH="/ex/confluence/<your-cloud-id>/wiki/rest/api"
export CONFLUENCE_AUTH_TYPE="basic"
export CONFLUENCE_EMAIL="user@company.com"
export CONFLUENCE_API_TOKEN="your-scoped-token"
```

Required classic scopes for scoped tokens:
- Read-only: `read:confluence-content.all`, `read:confluence-content.summary`, `read:confluence-space.summary`, `search:confluence`
- Write: add `write:confluence-content`, `write:confluence-file`, `write:confluence-space`
- Attachments: `readonly:content.attachment:confluence` (download), `write:confluence-file` (upload)

**Read-only mode (recommended for AI agents):**

Prevents all write operations (create, update, delete, move, etc.) at the profile level. Useful when giving an AI agent access to Confluence for reading only.

```sh
# Via profile flag
confluence profile add agent --domain "company.atlassian.net" --token "xxx" --read-only

# Via environment variable (overrides config file)
export CONFLUENCE_READ_ONLY=true
```

When read-only mode is active, any write command exits with an error:
```
Error: This profile is in read-only mode. Write operations are not allowed.
```

`profile list` shows read-only profiles with a `[read-only]` badge.

---

## Page ID Resolution

Most commands accept `<pageId>` — a numeric ID or any of the supported URL formats below.

**Supported formats:**

| Format | Example |
|---|---|
| Numeric ID | `123456789` |
| `?pageId=` URL | `https://company.atlassian.net/wiki/viewpage.action?pageId=123456789` |
| Pretty `/pages/<id>` URL | `https://company.atlassian.net/wiki/spaces/SPACE/pages/123456789/Page+Title` |
| Display `/display/<space>/<title>` URL | `https://company.atlassian.net/wiki/display/SPACE/Page+Title` |

```sh
confluence read 123456789
confluence read "https://company.atlassian.net/wiki/viewpage.action?pageId=123456789"
confluence read "https://company.atlassian.net/wiki/spaces/MYSPACE/pages/123456789/My+Page"
```

> **Note:** Display-style URLs (`/display/<space>/<title>`) perform a title-based lookup, so the page title in the URL must match exactly. When possible, prefer numeric IDs or `/pages/<id>` URLs for reliability.

## Content Formats

| Format | Notes |
|---|---|
| `markdown` | Recommended for agent-generated content. Automatically converted by the API. |
| `storage` | Confluence XML storage format (default for create/update). Use for programmatic round-trips. |
| `html` | Raw HTML. |
| `text` | Plain text — for read/export output only, not for creation. |

---

## Commands Reference

See [commands-reference.md](commands-reference.md) for the full per-command reference
(`init`, `read`, `info`, `find`, `search`, `spaces`, `children`, `create`, `create-child`,
`update`, `move`, `delete`, `edit`, `export`, `attachments`, `attachment-upload`,
`attachment-delete`, `comments`, `comment`, `comment-delete`, `copy-tree`, `profile`,
`stats`, `convert`, `install-skill`).

---

## Common Agent Workflows

### Read → Edit → Update (round-trip)

```sh
# 1. Fetch raw storage XML
confluence edit 123456789 --output ./page.xml

# 2. Modify page.xml with your tool of choice

# 3. Push the updated content
confluence update 123456789 --file ./page.xml --format storage
```

### Build a documentation hierarchy

```sh
# Create root page, note the returned ID (e.g. 111222333)
confluence create "Project Overview" MYSPACE --content "# Overview" --format markdown

# Add children under it
confluence create-child "Architecture" 111222333 --content "# Architecture" --format markdown
confluence create-child "API Reference" 111222333 --file ./api.md --format markdown
confluence create-child "Runbooks" 111222333 --content "# Runbooks" --format markdown
```

### Copy a full page tree

```sh
# Preview first
confluence copy-tree 123456789 987654321 --dry-run

# Execute the copy
confluence copy-tree 123456789 987654321 "Backup Copy"
```

### Offline format conversion

```sh
# Convert markdown to Confluence storage format (no server needed)
confluence convert -i doc.md -o doc.xml --input-format markdown --output-format storage

# Convert storage format to markdown for editing
confluence convert -i page.xml -o page.md --input-format storage --output-format markdown
```

### Export a page for local editing

```sh
confluence export 123456789 --format markdown --dest ./local-docs
# => ./local-docs/<page-title>/page.md + ./local-docs/<page-title>/attachments/
```

### Process children as JSON

```sh
confluence children 123456789 --recursive --format json | jq '.[].id'
```

### Search and process results

```sh
confluence search --cql 'siteSearch ~ "release notes" and space = "MYSPACE"' --limit 20
```

---

## Agent Tips

- **Always use `--yes`** on destructive commands (`delete`, `comment-delete`, `attachment-delete`) to avoid interactive prompts blocking the agent.
- **Prefer `--format markdown`** when creating or updating content from agent-generated text — it's the most natural format and the API converts it automatically.
- **Use `--format json`** on `children` and `comments` for machine-parseable output.
- **ANSI color codes**: stdout may contain ANSI escape sequences. Pipe through `| cat` or use `NO_COLOR=1` if your downstream tool doesn't handle them.
- **Page ID vs URL**: numeric IDs and pretty `/pages/<id>` URLs are fully supported. Prefer them over display-style `/display/<space>/<title>` URLs, which perform a title-based lookup and fail if the title doesn't match exactly.
- **Cross-space moves**: `confluence move` only works within the same space. Moving across spaces is not supported.
- **Multiple instances**: Use `--profile <name>` or `CONFLUENCE_PROFILE` env var to target different Confluence instances without reconfiguring.
- **Read-only mode**: Set `CONFLUENCE_READ_ONLY=true` or use `--read-only` when creating profiles to prevent accidental writes. This is enforced at the CLI level — all write commands will be blocked.

## Error Patterns

| Error | Cause | Fix |
|---|---|---|
| `No configuration found` | No config file and no env vars set | Set env vars or run `confluence init` |
| `Cross-space moves are not supported` | `move` used across spaces | Copy with `copy-tree` instead |
| 400 on inline comment creation | Editor metadata required | Use `--location footer` or reply to existing inline comment with `--parent` |
| `File not found: <path>` | `--file` path doesn't exist | Check the path before calling the command |
| `At least one of --title, --file, or --content must be provided` | `update` called with no content options | Provide at least one of the required options |
| `Profile "<name>" not found!` | Specified profile doesn't exist | Run `confluence profile list` to see available profiles |
| `Cannot delete the only remaining profile.` | Tried to remove the last profile | Add another profile before removing |
| `This profile is in read-only mode` | Write command used with a read-only profile | Use a writable profile or remove `readOnly` from config |
