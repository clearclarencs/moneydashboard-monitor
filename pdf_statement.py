from tabula import read_pdf
import os
from datetime import datetime

class pdfReader:
    def addTransactions(self, groups):
        if not self.check():
            return groups
        
        self.groups = groups

        self.read()
        self.add()

        os.remove("temp.pdf")

        return self.groups


    def read(self):
        try:
            self.raw = "\n".join([str(x) for x in read_pdf("temp.pdf", stream=True, guess=True, pages='all',
                                multiple_tables=True,
                                pandas_options={'header':None}
                                )])
        except Exception:
            self.raw = []
    
    def check(self):
        return os.path.exists("temp.pdf")
    
    def add(self):
        for trans in self.raw.splitlines():
            try:
                components = trans.split()
                day = int(components[1])
                month = components[2]
                year = int(components[3])
                description = components[4]
                income = bool("-" not in components[5])
                amount = float(components[5].split("£")[1])
                formatted_date = datetime.strptime(f"{day}/{month}/{year}", "%d/%b/%Y").strftime("%d/%m/%y")
                bank = "Chase"
            except Exception:
                continue

            transaction = {
                "amount":{
                    "amount": amount
                 },
                "type": ("Credit" if income else "Transaction"),
                "account_alias": bank,
            }

            key = (description, formatted_date)

            try:
                self.groups[key].append(transaction)
            except KeyError:
                self.groups[key] = [transaction]