import os

from tabula import read_pdf
from datetime import datetime
from glob import glob

class pdfReader:
    def addTransactions(self, groups):
        if not self.check():
            return groups
        
        self.groups = groups

        self.read()
        self.add()

        for filename in glob("*.pdf"):
            os.remove(filename)

        return self.groups


    def read(self):
        try:
            self.raw = []

            for filename in glob("*.pdf"):
                self.raw += [str(x) for x in read_pdf(filename, stream=True, pages='all',
                                    multiple_tables=True,
                                    guess=False,
                                    pandas_options={'header':None}
                                    )]
            
            self.raw = "\n".join(self.raw)
        except Exception as e:
            print(e)
            self.raw = []
    
    def check(self):
        return bool(glob("*.pdf"))
    
    def add(self):
        for trans in self.raw.splitlines():
            try:
                component1, component2, balance = [x.split() for x in trans.split("£")]
                day = int(component1[1])
                month = component1[2]
                year = int(component1[3])
                description = " ".join(component1[4:-1]).replace(" NaN", "")
                income = bool("-" not in component2)
                amount = float(component2[0])
                formatted_date = datetime.strptime(f"{day}/{month}/{year}", "%d/%b/%Y").strftime("%d/%m/%y")
                bank = "Chase"
            except Exception as e:
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