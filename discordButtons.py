import discord
import dateutil.parser

from settingsManager import config


class Buttons(discord.ui.View):
    def __init__(self, moneyDashboardMonitor, googleSheet, transaction_group, embed, *, timeout=None):
        self.transaction_group = transaction_group
        self.moneyDashboardMonitor = moneyDashboardMonitor
        self.googleSheet = googleSheet
        self.embed = embed
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Business", style=discord.ButtonStyle.blurple)
    async def business_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 368603
        self.embed.set_author(name=f"Business - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        self.googleSheet.add_transactions([self.transaction_group])

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

        config.add_to_list(self.transaction_group['description'])

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.green)
    async def whitelist_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        self.embed.color = 5763719
        self.embed.set_author(name=f"Whitelist - {self.transaction_group['description']}")
        await interaction.response.edit_message(embed=self.embed, view=None)

        config.add_to_list(self.transaction_group['description'], blacklist=False)

        self.googleSheet.add_transactions([self.transaction_group])


class ButtonsWithSplit(Buttons):
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
        
        await self.moneyDashboardMonitor.ask_transactions(new_transactions)