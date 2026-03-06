# Fork Workflow

## Start Working on an Assigned Issue

### 1. Ensure your fork is up to date

```bash
# Add the upstream remote (if you haven't already)
git remote add upstream https://github.com/ORIGINAL_OWNER/catalog.git

# Fetch and sync with upstream main
git fetch upstream
git checkout main
git merge upstream/main
```

### 2. Create a feature branch

```bash
git checkout -b issue-123-short-description
```

### 3. Do your work, commit, and push to your fork

```bash
git add <files>
git commit -m "Fix: short description of change"
git push origin issue-123-short-description
```

### 4. Open a Pull Request

- Go to your fork on GitHub
- Click **"Compare & pull request"**
- Set the **base repository** to the original repo and **base branch** to `main`
- Reference the issue in your PR description (e.g., `Closes #123`)

---

## Update Your Fork After a PR is Merged

```bash
# Fetch upstream changes
git fetch upstream

# Switch to main and merge
git checkout main
git merge upstream/main

# Push the updated main to your fork
git push origin main
```

Optionally, clean up your feature branch:

```bash
git branch -d issue-123-short-description
git push origin --delete issue-123-short-description
```
