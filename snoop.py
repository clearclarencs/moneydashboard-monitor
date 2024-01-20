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
                "platform":"Apple",
                "udid":"vkuyvhjjhbiiug"
            },
            "pin":settings["snoopPin"]
        }
        resp = self.session.put("https://shared-services-api.snoop.app/customer/auth/verify", json=login_data).json()

        self.session.headers.update({"Authorization": f"Bearer {resp['accessToken']}"})

        if resp["isNewDevice"]: # Need to 2fa
            self.session.post("https://shared-services-api.snoop.app/customer/auth/verify-device")

            twoFA_data = {"code": input("Two factor code: ")}

            resp = self.session.put("https://shared-services-api.snoop.app/customer/auth/verify-device", json=twoFA_data).json()
            self.session.headers.update({"Authorization": f"Bearer {resp['accessToken']}"})

    
    def get_transactions(self):  # return {transaction_description: [transactions]}
        global sorted_transaction_ids

        accounts = {x["id"]:x["displayName"] for x in self.session.get("https://shared-services-api.snoop.app/financial-account/accounts").json()}

        r = self.session.get("https://shared-services-api.snoop.app/transaction/transactions?limit=100")

        grouped_transactions = {}

        for transaction in r.json()["transactions"]:
            if transaction["amount"] == 0 or transaction["transactionId"] in sorted_transaction_ids:
                continue

            transaction.update({
                "account_alias": accounts[transaction["accountId"]],
                "type": ("Credit" if transaction["amount"] > 0 else "Transaction"),
                "amount":{
                    "amount": abs(transaction["amount"])
                 },
                "id": transaction["transactionId"]
                })

            key = (transaction['description'], dateutil.parser.isoparse(transaction["timestamp"]).strftime("%d/%m/%y"))

            try:
                grouped_transactions[key].append(transaction)
            except KeyError:
                grouped_transactions[key] = [transaction]

            sorted_transaction_ids.append(transaction["transactionId"])
        
        sorted_transaction_ids = [x["transactionId"] for x in r.json()["transactions"]]
        
        return grouped_transactions