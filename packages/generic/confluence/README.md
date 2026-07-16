# confluence

Use confluence-cli to read, search, create, update, move, delete, and convert Confluence pages and attachments from the terminal.

## Installation

```bash
apm install Flutter-Global/apex-marketplace/packages/generic/confluence
```

## Usage

This skill is loaded automatically when Confluence operations are needed. Trigger phrases include: *read a Confluence page*, *search Confluence*, *create a Confluence page*, *update a Confluence page*, *confluence info*, *export from Confluence*, *confluence children*.

### Key capabilities

- **Read & search** — read page content, search by keyword or CQL, list children recursively
- **Write** — create top-level pages and child pages, update content, move pages
- **Delete** — trash pages, delete attachments and comments
- **Attachments** — list, download, and upload attachments
- **Export** — export a page and its attachments to a local directory
- **Format conversion** — convert between markdown, Confluence storage XML, HTML, and plain text offline
- **Profile management** — manage multiple Confluence instances via named profiles

### Configuration

The skill expects the following environment variables to be set:

| Variable | Description |
|---|---|
| `CONFLUENCE_DOMAIN` | Your Confluence hostname (e.g. `company.atlassian.net`) |
| `CONFLUENCE_API_PATH` | REST API base path (e.g. `/wiki/rest/api`) |
| `CONFLUENCE_AUTH_TYPE` | `basic` or `bearer` |
| `CONFLUENCE_EMAIL` | Email address (basic auth only) |
| `CONFLUENCE_API_TOKEN` | API token or personal access token |

See the skill documentation for full configuration options including scoped tokens, read-only mode, and multi-instance profiles.

## Version History

See [CHANGELOG.md](CHANGELOG.md)

## License

MIT - Internal use for Flutter-Global
