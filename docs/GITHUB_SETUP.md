# Publishing PipMora to GitHub

The authenticated GitHub connection can inspect and update an existing repository, but this session did not expose a *create repository* operation. The requested `faridbagheri/pipmora` repository was not found by the integration. No push or PR has been claimed.

1. In GitHub, create an **empty private** repository named `pipmora` under `faridbagheri` (do not initialize it with an extra README, .gitignore, or license).
2. Grant the ChatGPT GitHub integration access to this repository if GitHub asks you to select repositories.
3. To upload from the included local Git repository:

```bash
cd pipmora
git remote add origin https://github.com/faridbagheri/pipmora.git
git push -u origin main
```

If using the accompanying `pipmora-history.bundle` instead of the source ZIP, preserve the commits with:

```bash
git clone pipmora-history.bundle pipmora
cd pipmora
git remote add origin https://github.com/faridbagheri/pipmora.git
git push -u origin main
```

GitHub credentials belong in your local Git credential manager or GitHub's interactive authentication, never in files or commands saved to the repository. Once the repo exists, CI runs on the main branch and future changes should be submitted from feature branches through pull requests.
