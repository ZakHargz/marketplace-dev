---
name: jira
description: >
  Use this skill whenever the user mentions Jira, Jira tickets, issues, sprints,
  boards, epics, or stories — including searching for tickets, creating issues,
  updating issue fields, moving issues through workflow states (e.g. "move to In
  Progress", "close this ticket"), checking sprint progress, assigning issues, or
  any other Jira-related operation. Trigger even for casual mentions like "can you
  find that Jira ticket", "create a story for X", "what's in the current sprint",
  or "mark PROJ-123 as done". Also trigger when the user asks to set up Jira CLI
  or configure their Jira connection. Always use this skill for Jira work rather
  than attempting to call the Jira REST API directly with curl.
---

# Jira Skill

Help the user interact with Jira from the terminal using `jira`
([jira-cli](https://github.com/ankitpokhrel/jira-cli)).

**Announce at start:** "I'm using the jira skill. Let me check your setup first."

---

## Step 0: Check setup

```bash
# Is the CLI installed?
which jira && jira version

# Is it configured?
jira me
```

- If `which jira` fails → follow **Install** below
- If `jira me` errors → follow **Configure** below
- If both succeed → skip straight to the user's request

---

## Setup

### Install

**macOS:**
```bash
brew install jira-cli
```

**Other platforms:** See https://github.com/ankitpokhrel/jira-cli#installation

---

### Configure

Run the interactive setup wizard:

```bash
jira init
```

This prompts for:
1. Jira server URL (e.g. `yourcompany.atlassian.net`)
2. Login type: API token (Cloud) or bearer token (Server/DC)
3. Email address
4. API token — tell the user: "Go to https://id.atlassian.com/manage-profile/security/api-tokens, click **Create API token**, give it a name like `jira-cli`, and paste the value when prompted."

Config is saved to `~/.config/.jira/.config.yml`. To use a different config file:
```bash
jira --config /path/to/.config.yml <command>
# or: export JIRA_CONFIG_FILE=/path/to/.config.yml
```

#### Verify

```bash
jira me          # shows authenticated user
jira serverinfo  # shows Jira instance info
```

---

## Search & view issues

```bash
# Interactive explorer (default)
jira issue list

# Filter flags
jira issue list -tBug -yHigh -s"In Progress"
jira issue list -a"me@example.com"          # by assignee
jira issue list -l"backend" -l"urgent"      # by label(s)
jira issue list --created week              # created this week
jira issue list --updated today

# Free-text search (same as Jira UI search box)
jira issue list "login button broken"

# Raw JQL
jira issue list -q"project = PLAT AND assignee = currentUser() AND statusCategory != Done"

# Plain table output (scriptable)
jira issue list --plain
jira issue list --plain --no-headers
jira issue list --plain --columns key,summary,status,assignee

# JSON / CSV
jira issue list --raw
jira issue list --csv

# Paginate: <from>:<limit>
jira issue list --paginate 0:50

# View a specific issue
jira issue view KEY-123
jira issue view KEY-123 --comments 5   # show 5 comments
jira issue view KEY-123 --raw          # raw JSON

# Open in browser
jira open KEY-123
```

**Useful JQL patterns:**

| Goal | JQL |
|---|---|
| My open issues | `assignee = currentUser() AND statusCategory != Done` |
| Open high-priority bugs | `issuetype = Bug AND priority = High AND status != Done` |
| Issues updated today | `updated >= startOfDay()` |
| Active sprint | `sprint in openSprints()` |
| Unassigned | `assignee is EMPTY` |

---

## Create & update issues

### Create

```bash
# Interactive (prompts for missing fields)
jira issue create

# Non-interactive
jira issue create -tBug -s"Login button broken" -yHigh -l"frontend" -b"Description here"
jira issue create -tStory -s"Add rate limiting" -p PLAT --no-input

# With parent (epic or parent issue)
jira issue create -tTask -s"Subtask" -P PLAT-100 --no-input

# From template file
jira issue create --template /path/to/template.tmpl

# From stdin
echo "Description from stdin" | jira issue create -s"Summary" -tTask --no-input

# Custom fields
jira issue create -tStory -s"Story with points" --custom story-points=3

# Open in browser after creation
jira issue create -tBug -s"New bug" --web

# JSON output (returns created issue key)
jira issue create -tTask -s"..." --raw
```

Common types: `Epic`, `Story`, `Task`, `Bug`, `Subtask`

### Edit

```bash
# Edit summary, priority, labels etc.
jira issue edit KEY-1 -s"Updated title" --no-input
jira issue edit KEY-1 -yLow -b"New description" --no-input

# Append labels
jira issue edit KEY-1 -l"backend"

# Remove a label (prefix with -)
jira issue edit KEY-1 --label -urgent

# Change assignee
jira issue edit KEY-1 -a"colleague@example.com" --no-input
```

### Assign

```bash
jira issue assign KEY-1 "me@example.com"
jira issue assign KEY-1 "$(jira me)"   # assign to self
jira issue assign KEY-1 default         # assign to default assignee
jira issue assign KEY-1 x               # unassign
```

### Comments

```bash
jira issue comment add KEY-1 --body "Looking into this now"

# From stdin
echo "Comment text" | jira issue comment add KEY-1
```

---

## Transitions (workflow)

```bash
# Move to a state
jira issue move KEY-1 "In Progress"
jira issue move KEY-1 Done

# With comment and assignee
jira issue move KEY-1 Done --comment "Resolved in v1.2" --assignee "me@example.com"
```

**Note:** State names must match your project's workflow exactly. If unsure, check the Jira UI or `jira issue view KEY-1` for current status.

---

## Sprints & boards

```bash
# List boards in project
jira board list

# List sprints (interactive)
jira sprint list

# List sprints as table
jira sprint list --table --plain

# View issues in active sprint
jira sprint list --current

# View issues in a specific sprint
jira sprint list <SPRINT_ID>
jira sprint list <SPRINT_ID> --plain --columns key,summary,status,assignee

# Filter sprint issues with JQL
jira sprint list <SPRINT_ID> -q"assignee = currentUser()"

# Previous / next sprint
jira sprint list --prev
jira sprint list --next

# Add issue(s) to a sprint
jira sprint add <SPRINT_ID> KEY-1 KEY-2
```

---

## Epics

```bash
# List epics
jira epic list

# Create an epic
jira epic create -s"Epic title" -b"Description"

# Add issues to an epic
jira epic add EPIC-1 KEY-2 KEY-3

# Remove issue from epic
jira epic remove KEY-2
```

---

## Projects

```bash
jira project list
```

---

## Useful patterns

| Task | Command |
|---|---|
| My open issues | `jira issue list -q"assignee = currentUser() AND statusCategory != Done" --plain` |
| Active sprint issues | `jira sprint list --current --plain` |
| Unassigned bugs | `jira issue list -tBug -ax --plain` |
| Issues updated today | `jira issue list --updated today --plain` |
| Export to CSV | `jira issue list --csv > issues.csv` |
| Open issue in browser | `jira open KEY-123` |
| Raw JSON | `jira issue list --raw` |
| Assign to self | `jira issue assign KEY-1 $(jira me)` |
