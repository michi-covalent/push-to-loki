# push-to-loki

This action pushes information about GitHub Actions workflow runs to Loki.
This action is designed to be triggerd using the
[workflow_run](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
event.

## Inputs

### endpoint (required)

Loki endpoint (e.g. `https://logs-prod3.grafana.net/loki/api/v1/push`).

### username (required)

Loki username.

### password (required)

Loki password.

### workflow_run_url (optional)

Github Actions workflow run URL. Defaults to `${{ github.event.workflow_run.url }}`.

### token (optional)

GitHub token to use for accessing workflow run and jobs URLs. Defaults to `${{ github.token }}`.
For private repositories, this action needs `read` permission for `actions` scope:

```
permissions:
  actions: read
```

See [GitHub Docs](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)
for more information about GitHub token permissions.

## Example usage

See [push.yml](.github/workflows/push.yml) for an example usage.
