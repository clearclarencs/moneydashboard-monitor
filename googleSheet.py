from settingsManager import config
import gspread

class googleSheet:
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