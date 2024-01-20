from settingsManager import config, sorted_transaction_ids
from pycognito.aws_srp import AWSSRP
import dateutil.parser
import boto3
import datetime
import requests
import botocore

session_config = botocore.config.Config(
  user_agent="aws-amplify/0.1.x js",
)

settings = config.get_config()

if settings.get("proxy"):
    session_config.proxies = {'https': settings["proxy"]}

class moneyDashboard:
    def __init__(self):
        self.session = requests.session()

        self.session.headers.update({
            "X-Api-Key": "Yk3HYHf7oD1R4j7aJYMp8CG2ruiDSZk4hbV10Vj3",
            "X-Snoop-Version": "7.1.1",
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "content-type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/4.9.3"
        })

    def login(self):  # Token lasts 1 hour
        settings = config.get_config()


        login_data = {
            "customerId":settings["snoopCustomerID"],
            "device":{
                "advertisingId":"1",
                "appsFlyerId":"1",
                "make":"G",
                "model":"sdk_gphone_arm",
                "osVersion":"20",
                "platform":"Web",
                "udid":"jhsdbld"
            },
            "pin":settings["snoopPin"]
        }
        self.session.put("/customer/auth/verify")

        

        

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

            key = (transaction['description'], dateutil.parser.isoparse(transaction["created"]).strftime("%d/%m/%y"))

            try:
                grouped_transactions[key].append(transaction)
            except KeyError:
                grouped_transactions[key] = [transaction]

            sorted_transaction_ids.append(transaction["id"])
        
        sorted_transaction_ids = [x["id"] for x in r.json()]
        
        return grouped_transactions