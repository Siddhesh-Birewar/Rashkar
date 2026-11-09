# Rashkar — GitHub Release Preparation & Pre-Push Audit

## Phase 0: Work Preservation and Environment Baseline

- **Repository Root**: `D:\CSE AIML\Rashkar`
- **Initial HEAD Commit**: `0d891d4` (`fix(heat-risk): correct threshold messaging, shift coverage warning, provenance, crop expiry handling, and add 14 regression tests`)
- **Current Active Branch**: `master`
- **Safety Backup Tag**: `pre-github-cleanup-20261109`
- **Configured Remote**: `origin` -> `https://github.com/Vernit185/Rashkar.git`
- **Target Remote Branch**: `yeild-and-heat-risk-feature`
- **Worktree Condition**: 
  - Working tree contains tracked local development database `rashkar_dev.db` which will be safely untracked (`git rm --cached`) and ignored via `.gitignore` to prevent committing binary SQLite data or local session artifacts.
  - All source files, models, and test suites are intact at `0d891d4`.

---
