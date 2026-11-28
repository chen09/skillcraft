# Third-party skill overlays

Small, environment-neutral additions that this user's machines apply on top of third-party skills. The upstream skills are not vendored here.

Each directory contains:

- `upstream.json`: upstream repository, path, the commit the overlay was verified against, and the upstream license.
- `section.md`: the section to add.

## Apply

1. Install the upstream skill from `repo`/`path` into the machine's canonical skills directory, following that machine's normal review and install procedure.
2. Insert `section.md` after the first H1 heading of the upstream `SKILL.md`, separated by one blank line on each side. Do not change the frontmatter.
3. If upstream has moved past `verifiedCommit`, review the upstream diff first. Reapply the section only if it still fits; otherwise update the overlay here.
4. Reload the skill through the host's skill tool and confirm the section is present.

## Overlays

- `find-skills` (vercel-labs/skills): canonical shared source and installation boundary.
- `test-driven-development` (obra/superpowers): do not delete existing work; delete-and-restart applies only to disposable exercise code.
- `writing-plans` (obra/superpowers): honor existing Strategy and authorization; tolerate missing `superpowers:` framework skills.
