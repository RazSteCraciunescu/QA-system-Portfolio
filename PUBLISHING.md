# Publishing this repository

## Suggested GitHub settings

**Repository name:** `distributed-systems-qa-portfolio`  
**Description:** `Senior QA portfolio: distributed services, API and interoperability testing, Docker, Pytest, Robot, Playwright, CI and release evidence.`

Suggested topics:

```text
quality-assurance test-automation pytest robot-framework playwright
api-testing integration-testing docker fastapi postgresql qa-portfolio
```

## First push with GitHub CLI

From this folder:

```bash
git init
git add .
git commit -m "Initial repository import"
git branch -M main
gh auth login
gh repo create distributed-systems-qa-portfolio --public --source=. --remote=origin --push
```

The GitHub CLI asks which account and authentication method to use, so no account name needs to be stored in this repository.

## First push using the GitHub website

1. Create an empty public repository named `distributed-systems-qa-portfolio`. Do not add a README, license, or `.gitignore` on GitHub.
2. Run the first four Git commands from the section above.
3. Run `git remote add origin`, add one space, and paste the HTTPS repository URL shown by GitHub.
4. Run `git push -u origin main`.

## Before making it public

- Review the README wording and keep only statements you are comfortable discussing in an interview.
- Run `python scripts/validate_repository.py`.
- Run the fast tests and, when Docker is available, the complete integration workflow.
- Enable GitHub Actions and package write permission only when publishing the container image.
