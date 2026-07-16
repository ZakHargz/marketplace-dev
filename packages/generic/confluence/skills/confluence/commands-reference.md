# confluence-cli Commands Reference

Full per-command reference for confluence-cli. See [SKILL.md](SKILL.md) for
configuration, page ID resolution, common workflows, and agent tips.

---

## `init`

Initialize configuration. Saves credentials to `~/.confluence-cli/config.json`.

```sh
confluence init [--domain <domain>] [--api-path <path>] [--auth-type basic|bearer] [--email <email>] [--token <token>] [--read-only]
```

All flags are optional; omitting any flag triggers an interactive prompt for that field. Provide all flags to run fully non-interactive. Use the global `--profile` flag to save to a named profile:

```sh
confluence --profile staging init --domain "staging.example.com" --auth-type bearer --token "your-token"
```

---

## `read <pageId>`

Read page content. Outputs to stdout.

```sh
confluence read <pageId> [--format html|text|storage|markdown]
```

| Option | Default | Description |
|---|---|---|
| `--format` | `text` | Output format: `html`, `text`, `storage`, or `markdown` |

```sh
confluence read 123456789
confluence read 123456789 --format storage
confluence read 123456789 --format markdown
```

---

## `info <pageId>`

Get page metadata. Use `--format json` for machine-readable output.

```sh
confluence info <pageId> [--format text|json]
```

```sh
confluence info 123456789
confluence info 123456789 --format json
```

---

## `find <title>`

Find a page by exact or partial title. Returns the first match.

```sh
confluence find <title> [--space <spaceKey>]
```

| Option | Description |
|---|---|
| `--space` | Restrict search to a specific space key |

```sh
confluence find "Architecture Overview"
confluence find "API Reference" --space MYSPACE
```

---

## `search <query>`

Search pages using a keyword or CQL expression.

```sh
confluence search [--cql] [--limit <number>] <query>
```

| Option | Default | Description |
|---|---|---|
| `--limit` | `10` | Maximum number of results |
| `--cql` | false | Pass query as raw CQL instead of text search |

```sh
confluence search "deployment pipeline"
confluence search --cql 'siteSearch ~ "deployment pipeline" and space = "MYSPACE"' --limit 50
```

---

## `spaces`

List accessible Confluence spaces (key and name).

```sh
confluence spaces
```

---

## `children <pageId>`

List child pages of a page.

```sh
confluence children <pageId> [--recursive] [--max-depth <number>] [--format list|tree|json] [--show-id] [--show-url]
```

| Option | Default | Description |
|---|---|---|
| `--recursive` | false | List all descendants recursively |
| `--max-depth` | `10` | Maximum depth for recursive listing |
| `--format` | `list` | Output format: `list`, `tree`, or `json` |
| `--show-id` | false | Show page IDs |
| `--show-url` | false | Show page URLs |

```sh
confluence children 123456789
confluence children 123456789 --recursive --format json
confluence children 123456789 --recursive --format tree --show-id
```

---

## `create <title> <spaceKey>`

Create a new top-level page or folder in a space.

```sh
confluence create <title> <spaceKey> [--content <string>] [--file <path>] [--format storage|html|markdown] [--type page|folder]
```

| Option | Default | Description |
|---|---|---|
| `--content` | — | Inline content string |
| `--file` | — | Path to content file |
| `--format` | `storage` | Content format |
| `--type` | `page` | Content type — `page` (default) or `folder`. Folders have no body. |

Either `--content` or `--file` is required for pages. Folders take no content — passing `--content` or `--file` with `--type folder` is rejected.

```sh
confluence create "Project Overview" MYSPACE --content "# Hello" --format markdown
confluence create "Release Notes" MYSPACE --file ./notes.md --format markdown
confluence create "Engineering Docs" MYSPACE --type folder
```

Outputs the new page (or folder) ID and URL on success.

---

## `create-child <title> <parentId>`

Create a child page or folder under an existing page. Inherits the parent's space automatically.

```sh
confluence create-child <title> <parentId> [--content <string>] [--file <path>] [--format storage|html|markdown] [--type page|folder]
```

Options are identical to `create`. Either `--content` or `--file` is required for pages; folders take no content.

```sh
confluence create-child "Chapter 1" 123456789 --content "Content here" --format markdown
confluence create-child "API Guide" 123456789 --file ./api.md --format markdown
confluence create-child "Sub-folder" 123456789 --type folder
```

---

## `update <pageId>`

Update an existing page's title and/or content. At least one of `--title`, `--content`, or `--file` is required.

```sh
confluence update <pageId> [--title <title>] [--content <string>] [--file <path>] [--format storage|html|markdown]
```

| Option | Default | Description |
|---|---|---|
| `--title` | — | New title |
| `--content` | — | Inline content string |
| `--file` | — | Path to content file |
| `--format` | `storage` | Content format |

```sh
confluence update 123456789 --title "New Title"
confluence update 123456789 --file ./updated.md --format markdown
confluence update 123456789 --title "New Title" --file ./updated.xml --format storage
```

---

## `move <pageId_or_url> <newParentId_or_url>`

Move a page to a new parent. Both pages must be in the same space.

```sh
confluence move <pageId_or_url> <newParentId_or_url> [--title <newTitle>]
```

| Option | Description |
|---|---|
| `--title` | Rename the page during the move |

```sh
confluence move 123456789 987654321
confluence move 123456789 987654321 --title "Renamed After Move"
```

---

## `delete <pageIdOrUrl>`

Delete (trash) a page by ID or URL.

```sh
confluence delete <pageIdOrUrl> [--yes]
```

| Option | Description |
|---|---|
| `--yes` | Skip confirmation prompt (required for non-interactive/agent use) |

```sh
confluence delete 123456789 --yes
```

---

## `edit <pageId>`

Fetch a page's raw storage-format content for editing locally.

```sh
confluence edit <pageId> [--output <file>]
```

| Option | Description |
|---|---|
| `--output` | Save content to a file (instead of printing to stdout) |

```sh
confluence edit 123456789 --output ./page.xml
# Edit page.xml, then:
confluence update 123456789 --file ./page.xml --format storage
```

---

## `export <pageId>`

Export a page and its attachments to a local directory.

```sh
confluence export <pageId> [--format html|text|markdown] [--dest <directory>] [--file <filename>] [--attachments-dir <name>] [--pattern <glob>] [--referenced-only] [--skip-attachments]
```

| Option | Default | Description |
|---|---|---|
| `--format` | `markdown` | Content format for the exported file |
| `--dest` | `.` | Base directory to export into |
| `--file` | `page.<ext>` | Filename for the content file |
| `--attachments-dir` | `attachments` | Subdirectory name for attachments |
| `--pattern` | — | Glob filter for attachments (e.g. `*.png`) |
| `--referenced-only` | false | Only download attachments referenced in the page content |
| `--skip-attachments` | false | Do not download attachments |

```sh
confluence export 123456789 --format markdown --dest ./docs
confluence export 123456789 --format markdown --dest ./docs --skip-attachments
confluence export 123456789 --pattern "*.png" --dest ./output
```

Creates a subdirectory named after the page title under `--dest`.

---

## `attachments <pageId>`

List or download attachments for a page.

```sh
confluence attachments <pageId> [--limit <n>] [--pattern <glob>] [--download] [--dest <directory>]
```

| Option | Default | Description |
|---|---|---|
| `--limit` | all | Maximum number of attachments to fetch |
| `--pattern` | — | Filter by filename glob (e.g. `*.pdf`) |
| `--download` | false | Download matching attachments |
| `--dest` | `.` | Directory to save downloads |

```sh
confluence attachments 123456789
confluence attachments 123456789 --pattern "*.pdf" --download --dest ./downloads
```

---

## `attachment-upload <pageId>`

Upload one or more files to a page. `--file` can be repeated for multiple files.

```sh
confluence attachment-upload <pageId> --file <path> [--file <path> ...] [--comment <text>] [--replace] [--minor-edit]
```

| Option | Description |
|---|---|
| `--file` | File to upload (required, repeatable) |
| `--comment` | Comment for the attachment(s) |
| `--replace` | Replace an existing attachment with the same filename |
| `--minor-edit` | Mark the upload as a minor edit |

```sh
confluence attachment-upload 123456789 --file ./report.pdf
confluence attachment-upload 123456789 --file ./a.png --file ./b.png --replace
```

---

## `attachment-delete <pageId> <attachmentId>`

Delete an attachment from a page.

```sh
confluence attachment-delete <pageId> <attachmentId> [--yes]
```

| Option | Description |
|---|---|
| `--yes` | Skip confirmation prompt |

```sh
confluence attachment-delete 123456789 att-987 --yes
```

---

## `comments <pageId>`

List comments for a page.

```sh
confluence comments <pageId> [--format text|markdown|json] [--limit <n>] [--start <n>] [--location inline,footer,resolved] [--depth all] [--all]
```

| Option | Default | Description |
|---|---|---|
| `--format` | `text` | Output format: `text`, `markdown`, or `json` |
| `--limit` | `25` | Maximum comments per page |
| `--start` | `0` | Start index for pagination |
| `--location` | — | Filter by location: `inline`, `footer`, `resolved` (comma-separated) |
| `--depth` | — | Leave empty for root-only; `all` for all nested replies |
| `--all` | false | Fetch all comments (ignores pagination) |

```sh
confluence comments 123456789
confluence comments 123456789 --format json --all
confluence comments 123456789 --location footer --depth all
```

---

## `comment <pageId>`

Create a comment on a page (footer or inline).

```sh
confluence comment <pageId> [--content <string>] [--file <path>] [--format storage|html|markdown] [--parent <commentId>] [--location footer|inline] [--inline-selection <text>] [--inline-original-selection <text>] [--inline-marker-ref <ref>] [--inline-properties <json>]
```

| Option | Default | Description |
|---|---|---|
| `--content` | — | Inline content string |
| `--file` | — | Path to content file |
| `--format` | `storage` | Content format |
| `--parent` | — | Reply to a comment by ID |
| `--location` | `footer` | `footer` or `inline` |
| `--inline-selection` | — | Highlighted selection text (inline only) |
| `--inline-original-selection` | — | Original selection text (inline only) |
| `--inline-marker-ref` | — | Marker reference (inline only) |
| `--inline-properties` | — | Full inline properties as JSON (advanced) |

Either `--content` or `--file` is required.

```sh
confluence comment 123456789 --content "Looks good!" --location footer
confluence comment 123456789 --content "See note" --parent 456 --location footer
```

> **Note on inline comments**: Creating a brand-new inline comment requires editor highlight metadata (`matchIndex`, `lastFetchTime`, `serializedHighlights`) that is only available in the Confluence editor. This metadata is not accessible via the REST API, so inline comment creation will typically fail with a 400 error. Use `--location footer` or reply to an existing inline comment with `--parent <commentId>` instead.

---

## `comment-delete <commentId>`

Delete a comment by its ID.

```sh
confluence comment-delete <commentId> [--yes]
```

| Option | Description |
|---|---|
| `--yes` | Skip confirmation prompt |

```sh
confluence comment-delete 456789 --yes
```

---

## `copy-tree <sourcePageId> <targetParentId> [newTitle]`

Copy a page and all its children to a new location.

```sh
confluence copy-tree <sourcePageId> <targetParentId> [newTitle] [--max-depth <depth>] [--exclude <patterns>] [--delay-ms <ms>] [--copy-suffix <suffix>] [--dry-run] [--fail-on-error] [--quiet]
```

| Option | Default | Description |
|---|---|---|
| `--max-depth` | `10` | Maximum depth to copy |
| `--exclude` | — | Comma-separated title patterns to exclude (supports wildcards) |
| `--delay-ms` | `100` | Delay between sibling creations in ms |
| `--copy-suffix` | `" (Copy)"` | Suffix appended to the root page title |
| `--dry-run` | false | Preview operations without creating pages |
| `--fail-on-error` | false | Exit with non-zero code if any page fails |
| `--quiet` | false | Suppress progress output |

```sh
# Preview first
confluence copy-tree 123456789 987654321 --dry-run

# Copy with a custom title
confluence copy-tree 123456789 987654321 "Backup Copy"

# Copy excluding certain pages
confluence copy-tree 123456789 987654321 --exclude "Draft*,Archive*"
```

---

## `profile list`

List all configuration profiles with the active profile marked.

```sh
confluence profile list
```

---

## `profile use <name>`

Switch the active configuration profile.

```sh
confluence profile use <name>
confluence profile use staging
```

---

## `profile add <name>`

Add a new configuration profile. Supports the same options as `init` (interactive, non-interactive, or hybrid).

```sh
confluence profile add <name> [--domain <domain>] [--api-path <path>] [--auth-type basic|bearer] [--email <email>] [--token <token>] [--protocol http|https] [--read-only]
```

Profile names may contain letters, numbers, hyphens, and underscores only.

```sh
confluence profile add staging --domain "staging.example.com" --auth-type bearer --token "xyz"
```

---

## `profile remove <name>`

Remove a configuration profile (prompts for confirmation). Cannot remove the only remaining profile.

```sh
confluence profile remove <name>
confluence profile remove staging
```

---

## `stats`

Show local usage statistics.

```sh
confluence stats
```

---

## `convert`

Convert between content formats locally without a Confluence server connection.

```sh
confluence convert [--input-file <path>] [--output-file <path>] --input-format <format> --output-format <format>
```

| Option | Default | Description |
|---|---|---|
| `--input-file`, `-i` | stdin | Input file path |
| `--output-file`, `-o` | stdout | Output file path |
| `--input-format` | — | Input format: `markdown`, `storage`, `html` (required) |
| `--output-format` | — | Output format: `markdown`, `storage`, `html`, `text` (required) |

Supported conversions: markdown→storage, markdown→html, markdown→text, html→storage, html→text, html→markdown, storage→markdown, storage→html, storage→text.

```sh
# Markdown to Confluence storage format
confluence convert -i doc.md -o doc.xml --input-format markdown --output-format storage

# Pipe via stdin/stdout
echo "# Hello" | confluence convert --input-format markdown --output-format storage

# Storage format back to markdown
confluence convert -i page.xml --input-format storage --output-format markdown
```

---

## `install-skill`

Copy the Claude Code skill documentation into your project's `.claude/skills/` directory so Claude Code can learn confluence-cli automatically.

```sh
confluence install-skill [--dest <directory>] [--yes]
```

| Option | Default | Description |
|---|---|---|
| `--dest` | `./.claude/skills/confluence` | Target directory |
| `--yes` | false | Skip overwrite confirmation |

```sh
confluence install-skill
```
