import json, requests, datetime, threading, asyncio, time
import dateutil.parser
import boto3
from pycognito.aws_srp import AWSSRP
import gspread
import discord
from discord.ext import commands 


with open("transactions.json", "r") as r:
    sorted_transaction_ids = json.loads(r.read())
running = False

def save_transactions():
    global sorted_transaction_ids
    with open("transactions.json", "r") as r:
        old_transactions = json.loads(r.read())

    while True:
        if old_transactions != sorted_transaction_ids:
            with open("transactions.json", "w") as w:
                w.write(json.dumps(sorted_transaction_ids))
            old_transactions = sorted_transaction_ids[:]
            print("Backed up transaction ID's")

        time.sleep(120)

threading.Thread(target=save_transactions, daemon=True).start()

client=commands.Bot(command_prefix="hjfdbjshdbfhsdbfjhdf", intents=discord.Intents.default())


class config:
    @staticmethod
    def get_config():
        with open("config.json", "r") as r:
            return json.loads(r.read())

    @staticmethod
    def edit_config(new_settings):
        with open("config.json", "r") as r:
            settings = json.loads(r.read())

        settings.update(new_settings)

        with open("config.json", "w") as w:
            w.write(json.dumps(settings, indent=4))


class Buttons(discord.ui.View):
    def __init__(self, classObj, transaction_group, embed, *, timeout=0):
        self.transaction_group = transaction_group
        self.classObj = classObj
        self.embed = embed
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Business", style=discord.ButtonStyle.blurple)
    async def business_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 368603
        self.embed.set_author(name=f"Business - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        self.classObj.add_transactions([self.transaction_group])

    @discord.ui.button(label="Personal", style=discord.ButtonStyle.grey)
    async def personal_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 10070709
        self.embed.set_author(name=f"Personal - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

    @discord.ui.button(label="Blacklist", style=discord.ButtonStyle.red)
    async def blacklist_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 15548997
        self.embed.set_author(name=f"Blacklist - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        self.classObj.add_to_list(self.transaction_group['description'])

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.green)
    async def whitelist_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 5763719
        self.embed.set_author(name=f"Whitelist - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        self.classObj.add_to_list(self.transaction_group['description'], blacklist=False)

        self.classObj.add_transactions([self.transaction_group])


    @discord.ui.button(label="Split", style=discord.ButtonStyle.grey)
    async def split_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 16705372
        self.embed.set_author(name=f"Split - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        new_transactions = []
        for transaction in self.transaction_group["transactions"]:
            new_transactions.append({
                "description": transaction["description"],
                "amounts": [transaction["amount"]],
                "accounts": transaction["account_alias"],
                "date": dateutil.parser.isoparse(transaction["created"]).strftime("%d/%m/%y"),
                "transactions": [transaction]
            })
        
        await self.classObj.ask_transactions(new_transactions)



class moneyDashboardMonitor:
    def __init__(self):
        self.session = requests.session()

        self.session.headers.update({
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://app.moneydashboard.com",
            "referer": "https://app.moneydashboard.com/",
            "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        })


    async def _daemon(self):
        while True:
            if int(datetime.datetime.utcnow().strftime("%H")) == 19:
                self.get_sheet()
                self.login()
                await self.sort_transactions()
                await asyncio.sleep(82800)
            else:
                await asyncio.sleep(3000)

    def add_to_list(self, description, blacklist=True):
        with open("config.json", "r") as r:
            settings = json.loads(r.read())
        
        colorlist = "businessBlacklist" if blacklist else "businessWhitelist"

        settings[colorlist].append(description)

        with open("config.json", "w") as w:
            w.write(json.dumps(settings, indent=4))


    ################################### Money dashboard logic

    def login(self):  # Token lasts 1 hour
        settings = config.get_config()

        client = boto3.client('cognito-idp', region_name="eu-west-2")
        
        aws = AWSSRP(username=settings["mdEmail"], password=settings["mdPassword"], pool_id="eu-west-2_oXtK9cXqF",
                    client_id='vj841jhgqv528ogqu71397g4', client=client)
                    
        tokens = aws.authenticate_user()

        self.session.headers.update({"x-auth": tokens["AuthenticationResult"]["IdToken"]})
    
    def get_transactions(self):  # return {transaction_description: [transactions]}
        global sorted_transaction_ids

        settings = config.get_config()

        user_accounts = self.session.get("https://neonapiprod.moneydashboard.com/v1/accounts").json()
        try:
            user_accounts = {x["accountId"]: x["alias"] for x in user_accounts}
        except Exception:
            raise RuntimeError(f"Error reading accounts, most likely login error: {user_accounts}")

        today = datetime.datetime.utcnow()

        data1 = {
            "startDate": (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            "endDate": today.strftime("%Y-%m-%d")
            }

        if settings["accounts"] != ["all"]:
            data1.update({"accounts": settings["accounts"]})
        
        r = self.session.post("https://neonapiprod.moneydashboard.com/v1/transactions/filter", json=data1)

        grouped_transactions = {}

        for transaction in r.json():
            if transaction["amount"]["amount"] == 0 or transaction["id"] in sorted_transaction_ids:
                continue

            transaction.update({"account_alias": user_accounts[transaction["accountId"]]})

            try:
                grouped_transactions[transaction["description"]].append(transaction)
            except KeyError:
                grouped_transactions[transaction["description"]] = [transaction]

            sorted_transaction_ids.append(transaction["id"])
        
        return grouped_transactions
    
    async def sort_transactions(self):
        settings = config.get_config()
        groups = self.get_transactions()

        good_transactions = []
        unsure_transactions = [] 
        other_income_transactions = []

        for description, transactions in groups.items():
            if description not in settings["businessBlacklist"]:
                amounts = []
                accounts = {}
                for i, transaction in enumerate(transactions):
                    amount = transaction["amount"]["amount"] if transaction["type"] == "Credit" else -transaction["amount"]["amount"]
                    amounts.append(amount)
                    accounts[transaction["account_alias"]] = ""
                    transactions[i]["amount"] = amount
                accounts = ", ".join(list(accounts))

                group = {
                        "description": description,
                        "amounts": amounts,
                        "accounts": accounts,
                        "date": dateutil.parser.isoparse(transactions[0]["created"]).strftime("%d/%m/%y"),
                        "transactions": transactions
                    }

                if description in settings["businessWhitelist"]:
                    good_transactions.append(group)
                elif description in list(settings["otherIncomes"]):
                    other_income_transactions.append(group)
                else:
                    unsure_transactions.append(group)

        if good_transactions:
            self.add_transactions(good_transactions)
        
        if other_income_transactions:
            self.add_income(other_income_transactions)
        
        if unsure_transactions:
            await self.ask_transactions(unsure_transactions)
    
    ################################### Google sheets logic

    def get_sheet(self):
        settings = config.get_config()

        gc = gspread.service_account(filename=settings["googleKeyPath"])

        # Open a sheet from a spreadsheet in one go
        self.sheet = gc.open_by_url(settings["googleSpreadsheet"]).get_worksheet(settings["worksheetNumber"])

    def add_income(self, other_income_transactions):
        settings = config.get_config()

        for group in other_income_transactions:
            cell = settings["otherIncomes"][group["description"]]

            value = self.sheet.get(cell, value_render_option="FORMULA").first()

            if type(value) is str:
                if value.lower().startswith("=sum(") and value.endswith(")"):
                    value = value[0:-1] + f", {', '.join([str(x) for x in group['amounts']])})"
                else:
                    value = value + f" + {' + '.join([str(x) for x in group['amounts']])}"
            else:
                value += sum(group["amounts"])

            self.sheet.update(cell, value, value_input_option="USER_ENTERED")
    
    def add_transactions(self, transactions):
        row = len(self.sheet.col_values(1))

        values = []

        for transaction in transactions:
            row += 1  # Iterate down
            values.append([
                transaction["description"],
                f"=SUM({', '.join([str(x) for x in transaction['amounts']])})",
                transaction["accounts"],
                transaction["date"]
                ])


        self.sheet.update(
            f'A{row}:D{row+len(transactions)-1}',
            values,
            value_input_option="USER_ENTERED"
        )
    
    ################################### Discord logic

    async def ask_transactions(self, transactions):
        settings = config.get_config()

        user = await client.fetch_user(int(settings["discordId"]))
        await user.create_dm()
        embed = discord.Embed(color=16777215)

        for transaction in transactions:
            embed.set_author(name=transaction["description"])
            embed.title = f"{len(transaction['transactions'])} transaction(s) totaling: £{sum(transaction['amounts'])}"
            embed.description = f"From account(s): {transaction['accounts']}"
            embed.set_footer(text=transaction['date'])
            
            await user.dm_channel.send(embed=embed, view=Buttons(self, transaction, embed))

            await asyncio.sleep(2)

@client.event
async def on_ready():
    global running
    if not running:
        running = True
        x = moneyDashboardMonitor()
        await x._daemon()

if __name__ == "__main__":
    settings = config.get_config()

    client.run(settings["botToken"])


