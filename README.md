# IBKR Dividend Email Notifier

This automated service connects to the Interactive Brokers (IBKR) Flex Web Service API to fetch a report of received dividends, generates a detailed HTML summary, and sends it via email.

## Features

- **IBKR Connection**: Securely fetches dividend data using IBKR's Flex Web Service.
- **Comprehensive Analysis**: Extracts information from both `ChangeInDividendAccrual` (accrued dividends) and `CashTransaction` (cash-paid dividends).
- **Professional HTML Report**: Generates a visually appealing and easy-to-read email with:
  - A summary of totals (gross, tax, net) consolidated in EUR.
  - A detailed table for each dividend, showing amounts in both their original currency and EUR.
  - Handling of multiple currencies and display of the exchange rates used.
- **Highly Configurable**: All settings (API credentials, SMTP) are managed through a `.env` file for better security and ease of maintenance.
- **Integrated Logging**: Logs service activity to the console and a file (`logs/dividend_service.log`) for easy debugging.
- **Pytest Tested**: Includes a test suite to ensure code reliability.

## Email Preview

The generated email has a clean and modern design. It includes:

1.  **Header**: With the title "Dividend Summary" and the corresponding date range.
2.  **Summary Cards**: Displaying the total gross dividend, taxes, and net dividend, all consolidated in Euros.
3.  **Detailed Table**: A table with each dividend received, specifying the Ticker, Company, and breakdowns of Gross, Tax, and Net in both the original currency (USD, GBP, etc.) and its EUR equivalent.
4.  **Footer**: Indicates the total number of dividends processed and the exchange rates applied in the report.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/IbkrTelegramMessageDividendos.git
    cd IbkrTelegramMessageDividendos
    ```

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

    - **On Windows:**
      ```bash
      venv\Scripts\activate
      ```
    - **On macOS/Linux:**
      ```bash
      source venv/bin/activate
      ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

To make the service work, it is crucial to configure the environment variables correctly.

1.  **Create a `.env` file** in the project root.

2.  **Add and configure the following variables in your `.env` file:**

    ```env
    #--- Interactive Brokers Credentials ---#
    # Your IBKR Flex Web Service token
    IBKR_FLEX_TOKEN="YOUR_TOKEN_HERE"
    # Your Flex Query ID for dividends
    IBKR_DIVIDENDS_QUERY_ID="YOUR_QUERY_ID_HERE"

    #--- Email (SMTP) Configuration ---#
    # SMTP server of your email provider (e.g., smtp.gmail.com)
    SMTP_SERVER="smtp.gmail.com"
    # SMTP port (587 for TLS is the most common)
    SMTP_PORT="587"
    # Email from which the emails will be sent
    SENDER_EMAIL="your_email@gmail.com"
    # Username for SMTP authentication (usually the same as the email)
    SMTP_USERNAME="your_email@gmail.com"
    # Your email password or, preferably, an app password
    SMTP_PASSWORD="YOUR_APP_PASSWORD"
    # Email that will receive the report
    RECIPIENT_EMAIL="recipient_email@domain.com"
    ```

### How to get IBKR credentials?

1.  **`IBKR_FLEX_TOKEN`**:

    - Log in to **Account Management** on the Interactive Brokers website.
    - Go to **Settings > Account Reporting > Flex Web Service**.
    - Enable the service and generate a new token. Copy the 256-character token.

2.  **`IBKR_DIVIDENDS_QUERY_ID`**:
    - In the same **Account Reporting** section, go to **Flex Queries**.
    - Create a new **Activity Flex Query**.
    - In the **"Change in Dividend Accruals"** section, select the fields: `date`, `symbol`, `description`, `grossAmount`, `tax`, `netAmount`, `currency`, `fxRateToBase`.
    - In the **"Cash Transactions"** section, select the fields: `dateTime`, `symbol`, `description`, `amount`, `currency`, `fxRateToBase`, `activityDescription`.
    - Save the query and copy the assigned ID number.

> **Important!** If you use Gmail, it is strongly recommended to generate an **"App Password"** in your Google account security settings and use it as `SMTP_PASSWORD` instead of your main password.

## Usage

To run the service manually, simply run the main script:

```bash
python main.py
```

This will execute the entire process: it will get the dividend data from IBKR, generate the report, and send the email.

### Automation (Cron Job)

To have the script run automatically every day, you can set it up as a `cron job` on Linux/macOS.

1.  Open the crontab editor:
    ```bash
    crontab -e
    ```
2.  Add a line to run the script at a specific time (e.g., at 8 AM every day), making sure to use absolute paths:
    ```cron
    # m h  dom mon dow   command
    0 8 * * * /absolute/path/to/your/venv/bin/python /absolute/path/to/your/project/main.py >> /absolute/path/to/your/project/logs/cron.log 2>&1
    ```
    This runs the script and redirects any output or errors to a specific log file for the cron job.

## Running Tests

The project includes tests to validate the logic of the IBKR client and the email generator. To run them:

```bash
pytest -v
```

### Automation with GitHub Actions

To automate the daily execution of the script using GitHub Actions, follow these steps:

#### 1. Project Structure

Make sure your repository has this structure:

```
your-repository/
├── .github/
│   └── workflows/
│       └── dividends.yml
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

#### 2. Create the Workflow

Create the file `.github/workflows/dividends.yml` with the following content:

```yaml
name: Daily IBKR Dividends

on:
  schedule:
    # Run every day at 08:00 UTC (09:00 CET/10:00 CEST)
    - cron: '0 8 * * *'
  workflow_dispatch:  # Allows manual execution

jobs:
  run-dividends:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run dividends script
      env:
        IBKR_FLEX_TOKEN: ${{ secrets.IBKR_FLEX_TOKEN }}
        IBKR_DIVIDENDS_QUERY_ID: ${{ secrets.IBKR_DIVIDENDS_QUERY_ID }}
        SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
        SMTP_PORT: ${{ secrets.SMTP_PORT }}
        SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
        SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
        SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
        RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
      run: |
        python main.py
        
    - name: Upload logs
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: dividends-logs
        path: |
          logs/*.log
          *.log
        retention-days: 7
```

#### 3. Configure Secrets

To keep your credentials secure, you must configure GitHub Secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click on **"New repository secret"** and add the following secrets:

| Secret Name | Description |
|---|---|
| `IBKR_FLEX_TOKEN` | Your IBKR Flex Web Service token |
| `IBKR_DIVIDENDS_QUERY_ID` | Your Flex Query ID for dividends |
| `SMTP_SERVER` | SMTP server (e.g., smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (e.g., 587) |
| `SENDER_EMAIL` | Email from which the emails will be sent |
| `SMTP_USERNAME` | Username for SMTP authentication |
| `SMTP_PASSWORD` | Email password or app password |
| `RECIPIENT_EMAIL` | Email that will receive the report |

#### 4. Customize the Schedule

The workflow is configured to run daily at 08:00 UTC. To change the schedule, modify the cron line:

```yaml
# Format: 'minute hour day month day_of_week'
# Examples:
- cron: '0 8 * * *'     # Daily at 08:00 UTC
- cron: '30 7 * * 1-5'  # Weekdays at 07:30 UTC
- cron: '0 9 * * 1'     # Only on Mondays at 09:00 UTC
```

**Timezone Conversion:**
- For Spain: UTC+1 (winter) / UTC+2 (summer)
- If you want execution at 09:00 Spanish time, use `'0 8 * * *'` (winter) or `'0 7 * * *'` (summer)

#### 5. Advantages of GitHub Actions

✅ **Free**: 2,000 minutes/month for public repositories
✅ **No network restrictions**: Full internet access (no issues with IBKR)
✅ **Reliable execution**: Robust GitHub infrastructure
✅ **Detailed logs**: Complete history of executions
✅ **Manual execution**: Button to run when you need
✅ **Notifications**: Automatic emails if the execution fails

#### 6. Test the Workflow

Once configured:

1. Push the changes to your repository
2. Go to the **Actions** tab on GitHub
3. Select your "Daily IBKR Dividends" workflow
4. Click on **"Run workflow"** to test it manually
5. Review the logs to verify that it works correctly

#### 7. Monitoring and Logs

- Logs are automatically saved as artifacts on GitHub
- They are kept for 7 days
- You can download them from the Actions tab → your execution → Artifacts
- GitHub will notify you by email if the workflow fails

#### 8. Important Considerations

⚠️ **Inactive repositories**: GitHub may pause workflows in repos with no activity for 60 days
⚠️ **Time limits**: Each job has a limit of 6 hours
⚠️ **Delays**: Scheduled workflows can have up to 15 minutes of delay during peak hours

#### Migration from Local Cron Job

If you are currently using a local cron job, GitHub Actions offers:
- Greater reliability (does not depend on your machine being on)
- Better maintenance (history of executions)
- Automatic error notifications
- Access from anywhere