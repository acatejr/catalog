# Docker Image Publishing Guide

## Triggering Rebuilds Without Creating Version Tags

You have several options to trigger a Docker image rebuild and republish to ghcr.io without creating a version tag:

### Option 1: Manual Workflow Dispatch (Easiest)

The workflow already has `workflow_dispatch` enabled, so you can manually trigger it from GitHub:

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click **Publish Docker Image** workflow (left sidebar)
4. Click **Run workflow** button (right side)
5. Select branch and click **Run workflow**

This will build and push with the `latest` tag.

### Option 2: Trigger on Push to Main Branch

Modify `.github/workflows/publish-docker.yml` to also trigger on pushes to main:

```yaml
on:
  push:
    branches:
      - main
    tags:
      - 'v*'
  workflow_dispatch:
```

This will automatically rebuild and push `latest` every time you push to main.

### Option 3: Add a Development Tag Pattern

You could use a pattern like `dev-*` or `test-*` for non-release builds:

```yaml
on:
  push:
    tags:
      - 'v*'        # Production releases
      - 'dev-*'     # Development builds
      - 'test-*'    # Test builds
  workflow_dispatch:
```

Then tag development builds:
```bash
git tag dev-$(date +%Y%m%d-%H%M%S)
git push origin --tags
```

## Recommended Approach

Use **Option 1** (manual dispatch) for ad-hoc testing, or **Option 2** if you want automatic builds on every commit to main.
