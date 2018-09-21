import schedule
import requests
import time

def do_auth_update():
    requests.get('http://127.0.0.1:5000/update_authority_index')


# set update scheduler
schedule.every().day.at("17:26").do(do_auth_update)

while True:
    schedule.run_pending()
    time.sleep(1)