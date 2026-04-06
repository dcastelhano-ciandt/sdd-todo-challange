---
description: Generate specs for all features listed in a roadmap file
allowed-tools: Read, Write, Bash, Glob, SlashCommand, TodoWrite
argument-hint: [roadmap-file] [--auto] [--filter <priority>]
---

# Spec Roadmap Generator

<background_information>
- **Mission**: Parse a roadmap Markdown file, extract feature items, and run `/sdd:spec-quick` for each one
- **Success Criteria**:
  - All features from the roadmap are converted into structured specs under `.sdd/specs/`
  - Each feature uses the same quality pipeline as `/sdd:spec-quick`
  - User controls execution mode: interactive (approve each feature) or automatic (`--auto`)
  - Already-existing specs are detected and skipped
</background_information>

<instructions>

## Core Task

Read a roadmap Markdown file, extract the list of features, and execute `/sdd:spec-quick` for each one in priority order.

---

## Step 1 — Parse Arguments

Parse `$ARGUMENTS`:

| Flag | Meaning |
|------|---------|
| (none) | Use `ROADMAP.md` in current directory, interactive mode |
| `--auto` | Automatic mode — no prompts between features |
| `--filter <priority>` | Only process features matching that priority label (e.g. `--filter "Priority 1"`) |
| First positional arg (not a flag) | Path to an alternative roadmap file |

Examples:
```
""                           → file=ROADMAP.md, mode=interactive
"--auto"                     → file=ROADMAP.md, mode=automatic
"docs/roadmap.md --auto"     → file=docs/roadmap.md, mode=automatic
"--filter 'Priority 1'"      → only Priority 1 features, interactive
```

---

## Step 2 — Read and Parse Roadmap

1. Use **Read** to load the roadmap file (default: `ROADMAP.md`)
2. Extract features using this heuristic:

   **Feature detection rule**: A feature is any `## ` level-2 heading that contains a feature name after a priority marker or dash.

   Examples of headings that qualify as features:
   ```markdown
   ## Priority 1 — Search
   ## Priority 2 — Due Dates + Overdue Filter
   ## 1. User Authentication
   ## Feature: Dark Mode
   ## Search
   ```

   For each matched heading:
   - **Feature label**: Full text after `—` or `-` or `:` or the full heading if no separator (e.g. `Search`, `Due Dates + Overdue Filter`)
   - **Priority**: Text before the separator if it starts with `Priority N` or a number (e.g. `Priority 1`, `Priority 2`)
   - **Goal line**: First `**Goal:**` paragraph under the heading (used to enrich the description)
   - **Description for spec-init**: Combine feature label + goal line for a richer init description

3. Apply `--filter` if provided: only keep features whose priority label matches (case-insensitive).

4. If no features found, report the issue and exit:
   ```
   ❌ No features found in ROADMAP.md
   Expected headings like: ## Priority 1 — Feature Name
   ```

---

## Step 3 — Check Existing Specs

For each extracted feature:
1. Convert feature label to kebab-case (same logic as `spec-quick`)
2. Use **Glob** to check `.sdd/specs/` for an existing spec with that name
3. Mark features that already have specs as `[SKIP]`

---

## Step 4 — Display Plan and Confirm

Show the execution plan:

```
📋 Roadmap: ROADMAP.md
   Mode: Interactive | Automatic

Features to process (N total, M skipped):
  ✅ [SKIP] search — spec already exists
  ⏳ due-dates-overdue-filter
  ⏳ labels-categories
  ⏳ subtasks
  ⏳ statistics-dashboard

Each feature runs: /sdd:spec-quick "<description>" [--auto]
```

**Interactive mode**: Ask "Proceed? (yes/no)" before starting.
**Automatic mode**: Display plan and start immediately after 2 seconds.

---

## Step 5 — Execute Feature Loop

For each feature marked `⏳` (not skipped):

1. **Update TodoWrite**: Mark current feature task as `in_progress`

2. **Display header**:
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🚀 [2/4] Due Dates + Overdue Filter
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

3. **Execute SlashCommand**:
   - Interactive mode: `/sdd:spec-quick "<feature label> — <goal line>"`
   - Automatic mode: `/sdd:spec-quick "<feature label> — <goal line>" --auto`

4. Wait for completion.

5. **Update TodoWrite**: Mark current feature task as `completed`

6. **Interactive mode**: Prompt "Continue to next feature? (yes/no)"
   - "no" → stop gracefully, show summary of completed features
   - "yes" → continue

7. **Automatic mode**: Immediately continue to next feature.

---

## Step 6 — Final Summary

After all features are processed (or user stopped early):

```
✅ Roadmap spec generation complete!

## Results:
- ✅ search — skipped (already exists)
- ✅ due-dates-overdue-filter — generated
- ✅ labels-categories — generated
- ✅ subtasks — generated
- ✅ statistics-dashboard — generated

## Generated Specs:
- .sdd/specs/due-dates-overdue-filter/
- .sdd/specs/labels-categories/
- .sdd/specs/subtasks/
- .sdd/specs/statistics-dashboard/

## Next Steps:
For each feature, run in order:
  /sdd:spec-impl <feature-name>

Or check status:
  /sdd:spec-status <feature-name>
```

---

## TodoWrite Task List

Initialize at the start with one task per non-skipped feature:

```json
[
  {"content": "Generate spec: due-dates-overdue-filter", "status": "pending"},
  {"content": "Generate spec: labels-categories", "status": "pending"},
  {"content": "Generate spec: subtasks", "status": "pending"},
  {"content": "Generate spec: statistics-dashboard", "status": "pending"}
]
```

---

## Important Constraints

- Never re-run spec-quick for a feature that already has a spec directory — skip it silently
- The description passed to spec-quick should be human-readable (not just the kebab-case name)
- In automatic mode, pass `--auto` to each spec-quick call
- In interactive mode, do NOT pass `--auto` to spec-quick — let the user control each spec
- Errors in one feature should not abort the entire roadmap — log the error and continue
- Respect the order features appear in the roadmap (top = first)

---

## Error Handling

| Error | Action |
|-------|--------|
| Roadmap file not found | Report path, suggest `ROADMAP.md` default |
| No features parsed | Show heading format hint, exit |
| spec-quick fails for one feature | Log error, mark task as failed, continue to next |
| User cancels in interactive mode | Show partial summary, suggest resume command |

</instructions>

## Tool Guidance

- **Read**: Load the roadmap file
- **Glob**: Check `.sdd/specs/*/` for existing specs
- **SlashCommand**: Execute `/sdd:spec-quick` per feature
- **TodoWrite**: Track progress per feature
- **Bash**: Only if needed for timestamp or path manipulation

## Output Description

Keep each phase header visible so the user can track progress across potentially many features. Show a clear separator between features. Final summary should list all processed specs with their paths for easy navigation.
