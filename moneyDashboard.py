from settingsManager import config, sorted_transaction_ids
from pycognito.aws_srp import AWSSRP
import boto3
import datetime
import requests

class moneyDashboard:
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