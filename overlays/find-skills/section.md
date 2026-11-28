## Shared Source And Installation Boundary

Use the target user's `.agent/skills` as the canonical shared source. Inspect source, license, commit and local differences before installation; preserve same-name local revisions. The CLI examples below describe upstream behavior, not permission to create tool-specific copies or update all skills indiscriminately. Stage reviewed files, install to the canonical source, then synchronize the already installed Codex/Claude/DSH discovery links using the receiver's existing procedure. Do not copy machine configuration or credentials.

When reconciling a locally modified copy with upstream, choose the merge base only from ancestors of the upstream HEAD; searching `--all` can match commits on unrelated branches. On Windows, apply a case-only rename by deleting the old file before writing the new one, or the old casing persists.
