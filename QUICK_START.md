# 🚀 Quick Start Guide - HydroWatch Pro

> **Silver Tier: Functional Assistant for Hydrology Monitoring**

---

## What You'll Get

- ✅ Autonomous flood monitoring system
- ✅ Email alerts with human approval
- ✅ Professional hydrology reports
- ✅ Qwen AI-powered decision making
- ✅ 24/7 monitoring via Windows Task Scheduler

---

## Prerequisites (5 minutes)

1. **Windows 10/11**
2. **Python 3.8+** (tested on 3.13)
3. **Qwen CLI** installed
4. **Gmail account** (for alerts)

---

## Step 1: Install Qwen CLI (2 minutes)

```bash
npm install -g @qwen-code/qwen-code
```

Verify installation:
```bash
qwen --version
```

---

## Step 2: Install Python Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

**Required packages:**
- pandas (data processing)
- watchdog (file monitoring)
- python-dotenv (environment variables)
- requests (HTTP calls)
- smtplib-ssl (email)
- pyperclip (clipboard)

---

## Step 3: Configure Email (3 minutes)

1. **Copy environment file:**
   ```bash
   copy .env.example .env
   ```

2. **Get Gmail App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Enable 2FA if not already enabled
   - Generate password for "Mail"
   - Copy the 16 characters (remove spaces)

3. **Edit `.env` file:**
   ```env
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_password
   ALERT_RECIPIENT=client@example.com
   ```

4. **Test email:**
   ```bash
   python mcp_email_server.py
   ```
   Check your inbox for test email.

---

## Step 4: Run the Agent (1 minute)

**Autonomous mode (24/7):**
```bash
python main.py
```

**Watcher mode (recommended):**
```bash
python main.py --watcher
```

**Manual workflow test:**
```bash
python main.py --run
```

---

## Step 5: Test with Sample Data (2 minutes)

1. **Create a CSV file** in `Hydrology-Vault/Inbox/`:

   ```csv
   River,Width_m,Depth_m,Velocity_mps
   Chenab,35,2.5,1.8
   Indus,55,3.5,2.2
   Ravi,28,1.8,1.4
   Jhelum,40,2.8,1.6
   ```

2. **Wait 10-20 seconds**

3. **Check results:**
   ```bash
   dir Hydrology-Vault\Done\report_*.md
   ```

4. **Open the report** - see professional hydrology analysis!

---

## Step 6: Test Flood Alert (if HIGH RISK)

If your data shows HIGH RISK (Q > 150 m³/s):

1. **Find approval file:**
   ```bash
   dir Hydrology-Vault\Needs_Action\APPROVAL_*.md
   ```

2. **Open the file** in Notepad

3. **Find this line:**
   ```
   DECISION: [type YES or NO here]
   ```

4. **Change to:**
   ```
   DECISION: YES
   ```

5. **Save the file**

6. **Wait 10 seconds**

7. **Check inbox** - flood alert email arrived!

---

## Command Reference

```bash
# Run autonomous mode (24/7)
python main.py

# Run all watchers (recommended)
python main.py --watcher

# Run single workflow manually
python main.py --run

# Generate LinkedIn post
python main.py --linkedin

# System health check
python main.py --health
```

---

## Folder Structure

```
Hydrology-Vault/
├── Inbox/                  # Drop CSV files here
├── Weather_Inbox/          # Weather bulletins here
├── Needs_Action/           # Approval requests wait here
├── Done/                   # Completed reports stored here
└── Dashboard.md            # System status (updates every 10s)
```

---

## What Happens Automatically

1. **CSV file dropped** → CSV Watcher detects it
2. **Action file created** → `HYDROLOGY_*.md` in `Needs_Action/`
3. **Orchestrator picks up** → Starts AI workflow
4. **Qwen AI creates plan** → `Plan_*.md` with reasoning
5. **Skills execute:**
   - Ingest data → Load CSV
   - Compute discharge → Q = W × D × V
   - Analyze risk → LOW/MEDIUM/HIGH
   - Send alert → Create approval request (if HIGH)
   - Generate report → Professional markdown
6. **Report saved** → `Done/report_*.md`
7. **Dashboard updated** → New count visible

---

## Troubleshooting

### Qwen CLI not found
```bash
# Install Node.js first, then:
npm install -g @qwen-code/qwen-code
```

### Email fails
- Verify 2FA is enabled on Gmail
- Generate new App Password
- Check `.env` has correct credentials

### No reports generated
- Check CSV has columns: `River`, `Width_m`, `Depth_m`, `Velocity_mps`
- Verify file is in `Hydrology-Vault/Inbox/`
- Check console for error messages

### Approval not processed
- Make sure `DECISION: YES` is exact format
- Ensure approval_watcher is running (use `--watcher` mode)

---

## Next Steps

1. **Set up scheduling** (optional):
   ```bash
   python schedule_setup.py
   ```
   Runs agent daily at 8:00 AM

2. **Add weather monitoring:**
   - Drop IMD weather bulletins in `Weather_Inbox/`
   - PDF Watcher extracts rainfall data automatically

3. **Configure LinkedIn** (optional):
   - See LINKEDIN_SETUP.md for API credentials
   - Auto-post professional updates

---

## Support

**Documentation:**
- README.md - Full project overview
- ARCHITECTURE.md - System design details
- .env.example - Configuration template

**Contact:**
- Email: zainabmukhtar2277@gmail.com
- GitHub: https://github.com/Zainab07-mm

---

*Estimated setup time: 10-15 minutes*
*First result: 2 minutes after dropping CSV file*
