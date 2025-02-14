import datetime, asyncio
import discord, random
from discord.ext import commands 

from settingsManager import config
from discordButtons import Buttons, ButtonsWithSplit
from googleSheet import googleSheet
from snoop import moneyDashboard
from pdf_statement import pdfReader

running = False

client = commands.Bot(command_prefix="!", intents=discord.Intents.default())

class moneyDashboardMonitor:
    def __init__(self):
        self.googleSheet = googleSheet()
        self.moneyDashboard = moneyDashboard()
        self.moneyDashboard.login() # Do an intialisation login incase of 2fa
        self.pdfReader = pdfReader()

    async def _daemon(self, hour=3):
        while True:
            if int(datetime.datetime.utcnow().strftime("%H")) == hour:
                self.googleSheet.get_sheet()

                await self.process_transactions()

                await asyncio.sleep(82800)
            else:
                await asyncio.sleep(3000)
    
    async def process_transactions(self):
        settings = config.get_config()

        self.moneyDashboard.login()
        groups = self.moneyDashboard.get_transactions()
        
        groups = self.pdfReader.addTransactions(groups)

        good_transactions = []
        unsure_transactions = [] 
        other_income_transactions = []

        for (description, day), transactions in groups.items():
            if description not in settings["businessBlacklist"]:
                amounts = []
                accounts = {}
                ids = ""
                for i, transaction in enumerate(transactions):
                    amount = transaction["amount"]["amount"] if transaction["type"] == "Credit" else -transaction["amount"]["amount"]
                    amounts.append(amount)
                    accounts[transaction["account_alias"]] = ""
                    transactions[i]["amount"] = amount
                    ids += transaction["id"]+","
                accounts = ", ".join(list(accounts))

                group = {
                        "description": description,
                        "amounts": amounts,
                        "accounts": accounts,
                        "ids": ids,
                        "date": day,
                        "transactions": transactions
                    }

                if description in settings["businessWhitelist"]:
                    good_transactions.append(group)
                elif description in list(settings["otherIncomes"]):
                    other_income_transactions.append(group)
                else:
                    unsure_transactions.append(group)

        if good_transactions:
            self.googleSheet.add_transactions(good_transactions)
        
        if other_income_transactions:
            self.googleSheet.add_income(other_income_transactions)
        
        if unsure_transactions:
            await self.ask_transactions(unsure_transactions)


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

            if len(transaction['transactions']) > 1:
                btn = ButtonsWithSplit
            else:
                btn = Buttons
            
            await user.dm_channel.send(embed=embed, view=btn(self, self.googleSheet, transaction, embed))

            await asyncio.sleep(2)

@client.event
async def on_ready():
    global running
    if not running:
        running = True
        x = moneyDashboardMonitor()
        await x._daemon()

@client.event
async def on_message(message):
    if isinstance(message.channel, discord.channel.DMChannel) and message.attachments and message.attachments[0].filename.endswith(".pdf"):
        await message.attachments[0].save(f"temp{random.randint(1,999999)}.pdf")


@client.event
async def on_command_error(ctx, error):
    pass

if __name__ == "__main__":
    client.run(config.get_config()["botToken"])


