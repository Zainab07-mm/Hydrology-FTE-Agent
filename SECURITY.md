# Security and Privacy

This is a prototype built for a hackathon. It has not had a security review. Read this page before you run it with any real data or accounts.

## Data in the repository

### Kept out of Git (through `.gitignore`)

- User CSV files in `Hydrology-Vault/Inbox/`
- Generated reports
- `.env` files and common secret patterns (`*.key`, `*.secret`, `credentials.json`)

### Public in the repository

- Source code (MIT License, see `LICENSE`)
- Sample data (`hydrology_data/sample.csv`)
- Documentation (README, architecture notes, quick start, handbook)
- Test scripts

## How credentials are handled

- Credentials are read from environment variables in a local `.env` file.
- The repository contains only `.env.example`, which holds placeholders.
- Never commit your own `.env` file.
- If you think an App Password or token has been exposed, revoke it and create a new one.

## Where your data goes

This project does not run entirely offline.

- **Qwen CLI:** prompts, which can include a preview of your data and the text of reports, are sent through the Qwen CLI. Depending on how the CLI is configured, this may go to a remote service. Check the CLI's settings and documentation before using data you do not want to share.
- **Gmail:** if you configure email alerts, the alert text is sent through Gmail SMTP. The Gmail watcher reads your inbox for CSV attachments if you enable it.
- **LinkedIn:** if you set `LINKEDIN_ACCESS_TOKEN`, the LinkedIn skill publishes the generated post to your profile through the API without a confirmation step. Leave the token unset to get a saved draft instead, and review any draft before you post it.

Everything else (reading CSV files, computing discharge, writing reports) runs on your own machine.

## Human approval

- Alert emails are only sent after a person changes the `DECISION` line in an approval file to `YES`.
- Generated text in reports and posts is written by an AI model and has not been reviewed by a hydrologist.
- Do not use this tool for real flood warnings.

## Recommendations

### For users

1. Keep your vault folder in a secure location.
2. Do not put sensitive CSV data in a public repository.
3. Use a separate Gmail account, not your main one, if you try the email alerts.
4. Read reports in `Hydrology-Vault/Done/` before you share them.

### For contributors

1. Never commit `.env` files or credentials.
2. Do not add user CSV files or generated logs to Git.
3. Keep generated reports out of version control.
4. List dependencies in `requirements.txt`.

## Known limitations

| Issue | Severity | Notes |
|-------|----------|-------|
| Qwen CLI is required | Low | Install with `npm install -g @qwen-code/qwen-code` |
| No validation of CSV data types | Low | Assumes numeric values in the measurement columns |
| Email and LinkedIn code untested on live accounts | Medium | Written, but never run against real accounts |
| LinkedIn posts publish without confirmation when a token is set | Medium | Leave the token unset to use draft mode |
| No security review or automated tests for security | Medium | Prototype only |

## Reporting a problem

For security concerns, contact: zainab.mukhtar077@gmail.com

---

Released under the MIT License. See the `LICENSE` file.
