=====README.MD =======

# SEO-Executive

A tri-level framework designed for the predictable and stable processing of business requirements.

## Architecture

The system operates on a three-tiered model:

1. **Tier 1: Guidelines** (`directives/`) - Protocols establishing the "what" and "how."
2. **Tier 2: Management** - AI-driven logic for routing and decisioning.
3. **Tier 3: Implementation** (`execution/`) - Code-based actions with consistent outcomes.

## Directory Structure

.
├── directives/          # Workflow documentation and Markdown specifications
├── execution/           # Python codebase for running specific actions
├── data/                # Configuration settings and source inputs
├── reports/             # Generated analytics (Spreadsheets)
├── .tmp/                # Transient files (excluded from version control)
├── .env                 # Secrets and environment configurations
├── credentials.json     # Authentication for Google OAuth (ignored)
├── token.json           # Session tokens for Google (ignored)
└── GEMINI.md            # System prompts and agent rules

## Setup

1. Populate `.env` with your API secrets and keys.
2. Place `credentials.json` and `token.json` in the root if Google integration is required.
3. Draft workflow protocols within the `directives/` folder.
4. Develop the necessary functional code within `execution/`.

## Key Principles

* **Cloud-First Outputs:** Final deliverables reside on cloud platforms (e.g., Slides, Sheets).
* **Ephemeral Storage:** Intermediate data is kept in `.tmp/` and is considered disposable/re-creatable.
* **Predictability:** Scripts are non-stochastic, reliable, and heavily documented.
* **Iterative Documentation:** Directives are evolving files that mature with the project.

## Self-Correction Loop

In the event of failure:

1. Resolve the specific error.
2. Patch the underlying script/tool.
3. Validate the fix through testing.
4. Refine the corresponding directive.
5. Resilience increases.

====WORKFLOW 1====

That can do keyword research for my SEO campaign. I will provide the seed keyword, location, and competitor domain. Competitor domain will be optional.

Based on these details, use data for SEO API to find the suitable keywords for my seed keyword and sort them based on their search volume.

Then if the user asks, create a Google Sheet that has keyword search volume, keyword difficulty. If the user asks to upload the sheet in the provided Google Drive folder, give the user the final Google Sheet link.

Here is my data for SEO API details:
