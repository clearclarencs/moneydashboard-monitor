# moneydashboard-monitor

Monedashboard is currently EOL, I might implement a new snoop app scraper when I get the chance. This is currently useless, however.
Snoop also has support for Chase though, meaning PDF statements aren't required anymore for me.
I believe they have SSL pinning and the web dashboard requires app 2fa though so it is a bit of a hurdle (if feasible at all).

A program to scrape your moneydashboard transactions daily.

The unknown transactions will then be dmed to you on discord to select whether they are business transactions.

Business transactions will be added to a google sheets spreadsheet.

For Chase transactions DM the pdf statement to the bot every month, the transactions will then be processed the following day.

# Setup
1) `pip install -r requirements.txt` (recommend running in a venv)
2) Create and download a gcloud key as [shown here](http://gspread.readthedocs.org/en/latest/oauth2.html)
3) Fill config.json as described below:

    "botToken" - Discord bot token, [tutorial here](https://www.writebots.com/discord-bot-token/) (need to share a server with bot to receive dm)
    
    "discordId" - Your discord account id for the bot to dm you
    
    "mdEmail" - Your money dashboard email
    
    "mdPassword" - Your money dashboard password
    
    "googleSpreadsheet" - Link to your google sheets spreadsheet
    
    "worksheetNumber" - The number of the worksheet to edit in the spreadsheet (starts at 0 left to right)
    
    "googleKeyPath" - Path to your gcloud key json as created in step 2
    
    "businessWhitelist" - List of whitelisted transaction descriptions to be added to spreadsheet
    
    "businessBlacklist"- List of blacklisted transaction descriptions to not be asked about
    
    "otherIncomes" - Repeated transaction descriptions that you want to be totalled in a single cell
    
    "accounts" - All the money dashboard bank account you want to be used (their ID's) ["all"] = all accounts
    
4) Run main.py

First run will read the previous 30 days of transactions.



This program uses floats to represent transaction amounts, while this is bad practice and can cause discrepancies, it is negligible for this application.
