# Agent Execution Protocol

## Mandatory lifecycle:

ANALYZE
PLAN
TEST (RED)
IMPLEMENT (GREEN)
REFACTOR
VALIDATE
COMMIT
DOCUMENT

## Quality Control

Before any commit, ensure the precommit hooks are executed.

## Requirements:

• Planning documents in docs/plans/
• Tests must exist before implementation
• All caches redirected to /tmp/$PROJECT
• Virtual environment must exist in /tmp/$PROJECT/.venv
• Commits must follow the Conventional Commits specification

## Confirm understanding
After reviewing this file confirm the location of temp files, and the shell script to run before any command.
