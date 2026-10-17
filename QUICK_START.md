# Quick Start Guide: HydroWatch Pro (Hydrology FTE Agent)

> A prototype that turns river measurement CSV files into discharge values, flow classifications and reports. Tested on sample data only.

---

## What You Get

- A watcher that picks up CSV files dropped into a folder
- Discharge calculation (Q = width x depth x velocity) and a low / moderate / high classification
- A markdown report for each file
- An email alert step that waits for a person to approve it (written, not tested on a live Gmail account)
- A Qwen model that decides which step runs next and writes the plain-language parts of the reports
- Optional scheduling through Windows Task Scheduler

This is a prototype. It has not been validated against observed river data and should not be used for real flood warnings.

---

## Prerequisites

1. Windows 10/11
2. Python 3.8+ (tested on 3.13)
3. Node.js, to install the Qwen CLI
4. A Gmail account, only if you want to try the email alerts

---

## Step 1: Install the Qwen CLI

```bash
npm install -g @qwen-code/qwen-code
```

Check the installation:

```bash
qwen --version
```

---

## Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

Main packages (the full list is in `requirements.txt`):

- pandas (data processing)
- watchdog (file monitoring)
- python-dotenv (environment variables)
- requests (HTTP calls)
- pyperclip (clipboard)

---

## Step 3: Configure email (optional)

You can skip this step. Without it, reports are still generated, and only the email alert step will not work.

1. Copy the environment file:

   ```bash
   copy .env.example .env
   ```

2. Get a Gmail App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Turn on 2-step verification first if it is off
   - Generate a password for "Mail"
   - Copy the 16 characters (remove the spaces)

3. Edit `.env`:

   ```env
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_password
   ALERT_RECIPIENT=recipient@example.com
   ```

4. Test the email module:

   ```bash
   python mcp_email_server.py
   ```

   Check the inbox for a test email. The email code has not been tested against a live account by the author, so report any errors you see.

---

## Step 4: Run the agent

Run all watchers (recommended):

```bash
python main.py --watcher
```

Main loop:

```bash
python main.py
```

Single workflow run:

```bash
python main.py --run
```

---

## Step 5: Try it with sample data

1. Save this as a CSV file in `Hydrology-Vault/Inbox/`. The values are invented for testing.

   ```csv
   River,Width_m,Depth_m,Velocity_mps
   Chenab,35,2.5,1.8
   Indus,55,3.5,2.2
   Ravi,28,1.8,1.4
   Jhelum,40,2.8,1.6
   ```

2. Wait a few seconds while the watcher picks up the file.

3. Check for the report:

   ```bash
   dir Hydrology-Vault\Done\report_*.md
   ```

4. Open the report to see the discharge calculation and classification for each river.

---

## Step 6: Try the approval step (only if a river is classified high)

A river is classified high when discharge is above 150 m3/s. This threshold is a demonstration value used for every river, not an official flood-stage limit.

1. Find the approval file:

   ```bash
   dir Hydrology-Vault\Needs_Action\APPROVAL_*.md
   ```

2. Open it in Notepad.

3. Find this line:

   ```
   DECISION: [type YES or NO here]
   ```

4. Change it to:

   ```
   DECISION: YES
   ```

5. Save the file and wait a few seconds with the watcher running.

6. If email is configured, check the recipient inbox. If it is not configured, the step will report an error.

---

## Command Reference

```bash
# Main loop
python main.py

# Run all watchers (recommended)
python main.py --watcher

# Run a single workflow manually
python main.py --run

# Generate a LinkedIn post draft
python main.py --linkedin

# System health check
python main.py --health
```

---

## Folder Structure

```
Hydrology-Vault/
├── Inbox/                  # Drop CSV files here
├── Weather_Inbox/          # Weather bulletin files
├── Needs_Action/           # Action files and approval requests
├── Done/                   # Completed reports
└── Dashboard.md            # Status file
```

---

## What Happens

1. A CSV file is dropped in `Inbox/` and the CSV watcher detects it.
2. An action file (`HYDROLOGY_*.md`) is created in `Needs_Action/`.
3. The orchestrator picks up the task.
4. Qwen writes a plan file (`Plan_*.md`).
5. The skills run:
   - Ingest data: load the CSV
   - Compute discharge: Q = W x D x V
   - Analyze flow: low, moderate or high
   - Send alert: create an approval request if high
   - Generate report: markdown
6. The report is saved to `Done/report_*.md`.
7. The dashboard is updated.

---

## Troubleshooting

### Qwen CLI not found

Install Node.js first, then:

```bash
npm install -g @qwen-code/qwen-code
```

### Email fails

- Check that 2-step verification is on for the Gmail account
- Generate a new App Password
- Check that `.env` has the right values

### No reports generated

- Check that the CSV has the columns `River`, `Width_m`, `Depth_m`, `Velocity_mps`
- Check that the file is in `Hydrology-Vault/Inbox/`
- Read the console output for error messages

### Approval not processed

- Make sure the line reads exactly `DECISION: YES`
- Make sure the approval watcher is running (use `--watcher` mode)

---

## Next Steps

1. Scheduling (optional):

   ```bash
   python schedule_setup.py
   ```

   This sets up a task in Windows Task Scheduler. Check the script for the run time before using it.

2. Weather files: put weather bulletin files in `Weather_Inbox/`. See `watchers/pdf_watcher.py` for the format it reads.

3. LinkedIn (optional): the LinkedIn code is written but has not been connected to an account. Set the token variables in `.env` (see `.env.example`). Without them, the tool saves a post draft and copies it to the clipboard. Read and correct any draft before you post it.

---

## Support

- README.md: project overview and limitations
- ARCHITECTURE.md: system design
- .env.example: configuration template

Contact: zainab.mukhtar077@gmail.com
GitHub: https://github.com/Zainab07-mm
