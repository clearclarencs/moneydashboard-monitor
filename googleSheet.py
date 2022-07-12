from settingsManager import config
import gspread

class googleSheet:
    def get_sheet(self):
        settings = config.get_config()

        gc = gspread.service_account(filename=settings["googleKeyPath"])

        # Open a sheet from a spreadsheet in one go
        self.sheet = gc.open_by_url(settings["googleSpreadsheet"]).get_worksheet(settings["worksheetNumber"])
    
    def add_to_value(self, value, additions):
        if type(value) is str:
            if value.lower().startswith("=sum(") and value.endswith(")"):
                value = value[0:-1] + f", {', '.join([str(x) for x in additions])})"
            else:
                value = value + f" + {' + '.join([str(x) for x in additions])}"
        else:
            value = f"=SUM({', '.join([str(x) for x in [value]+additions])})"
        
        if not value.startswith("="):
            value = f"={value}"
        
        return value

    def add_income(self, other_income_transactions):
        settings = config.get_config()

        for group in other_income_transactions:
            cell = settings["otherIncomes"][group["description"]]

            value = self.sheet.get(cell, value_render_option="FORMULA").first()

            value = self.add_to_value(value, group["amounts"])

            self.sheet.update(cell, value, value_input_option="USER_ENTERED")
    
    def add_transactions(self, transactions):
        for transaction in list(transactions):  # See if already a row with same desc and date to add to
            matching_description_rows = [i for i, x in enumerate(self.sheet.col_values(1)) if x == transaction["description"]]
            matching_date_rows = [i for i, x in enumerate(self.sheet.col_values(4)) if x == transaction["date"]]
            intersecting_rows = list(set(matching_description_rows).intersection(matching_date_rows))
            if intersecting_rows:
                intersecting_row = intersecting_rows[-1] + 1
                transactions.remove(transaction)

                value, cards = self.sheet.get(f"B{intersecting_row}:C{intersecting_row}", value_render_option="FORMULA")[0]

                cards = cards.split(", ")
                for account in transaction["accounts"].split(", "):
                    if account not in cards:
                        cards.append(account)
                cards = ", ".join(cards)

                value = self.add_to_value(value, transaction["amounts"])

                self.sheet.update(
                    f'B{intersecting_row}:C{intersecting_row}',
                    [[value, cards]],
                    value_input_option="USER_ENTERED"
                )

        row = len(self.sheet.col_values(1)) + 1

        values = []

        for transaction in transactions:
            values.append([
                transaction["description"],
                f"=SUM({', '.join([str(x) for x in transaction['amounts']])})",
                transaction["accounts"],
                transaction["date"]
                ])


        self.sheet.update(
            f'A{row}:D{row+len(values)-1}',
            values,
            value_input_option="USER_ENTERED"
        )