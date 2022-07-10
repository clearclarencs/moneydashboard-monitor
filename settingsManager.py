import json, threading, time

with open("transactions.json", "r") as r:
    sorted_transaction_ids = json.loads(r.read())

class config:
    @staticmethod
    def get_config():
        with open("config.json", "r") as r:
            return json.loads(r.read())

    @staticmethod
    def edit_config(new_settings):
        settings = config.get_config()

        settings.update(new_settings)

        with open("config.json", "w") as w:
            w.write(json.dumps(settings, indent=4))
    
    @staticmethod
    def add_to_list(description, blacklist=True):
        with open("config.json", "r") as r:
            settings = json.loads(r.read())
        
        colorlist = "businessBlacklist" if blacklist else "businessWhitelist"

        settings[colorlist].append(description)

        with open("config.json", "w") as w:
            w.write(json.dumps(settings, indent=4))

    @staticmethod
    def save_transactions_daemon():
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

transactions_daemon = threading.Thread(target=config.save_transactions_daemon, daemon=True)
transactions_daemon.start()