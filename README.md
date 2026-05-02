# Skillcraft

Reusable AI skills maintained by chen09.

This repository follows the standard skills repository layout: each directory under `skills/` is one self-contained skill with a `SKILL.md` file and optional bundled resources.

## Structure

```text
skillcraft/
├── README.md
├── LICENSE
├── .gitignore
└── skills/
    └── video-research-visual-report/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        └── scripts/
```

## Current Skills

- `skills/video-research-visual-report`: Convert a video into a researched text review plus visual report. It covers transcript extraction, original-source checking, external opinions, adversarial analysis, information images, long images, and PPT-style outputs.

## Install A Skill Locally

For Codex-style local skills:

```bash
mkdir -p ~/.codex/skills
ln -s /Volumes/WDC2T/Project/skillcraft/skills/video-research-visual-report ~/.codex/skills/video-research-visual-report
```

For other tools, copy or reference the relevant skill folder and its `SKILL.md`.

## Repository Rules

- Keep downloaded videos, generated images, transcripts, and temporary outputs out of git.
- Keep each skill self-contained under `skills/<skill-name>/`.
- Put reusable workflow instructions in `SKILL.md`.
- Put detailed prompts, checklists, and format notes in the skill's `references/`.
- Put deterministic helpers in the skill's `scripts/` when repeated manual code would be error-prone.
