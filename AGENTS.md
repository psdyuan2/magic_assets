# Commit Message Convention

All commits in this repository follow these rules. Agents (Hermes, Codex, Claude Code, Cursor, etc.) and humans alike must comply.

1. Write commit messages in concise **English**.
2. Use **Conventional Commits** format: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`.
3. Keep the subject line under **72 characters** whenever possible.
4. Describe the **actual code change**, not the agent, workflow, or task context.
5. **Never** include `[hermes]`, `[codex]`, `[cursor]`, agent names, or similar prefixes.
6. No long Chinese descriptions or verbose summaries.
7. Use imperative, action-oriented wording ("add", not "added" or "adds").

Examples:

- `feat: add Magic Assets skill`
- `fix: handle missing configuration`
- `docs: update installation guide`
- `refactor: simplify asset generation`
- `chore: organize skill directories`
