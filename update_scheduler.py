import schedule
import requests
import time
from base_url_config import BASE_URL

def do_auth_update():
    requests.get('http://{}/update/authorities'.format(BASE_URL))

def do_bib_update():
    requests.get('http://{}/update/bibs'.format(BASE_URL))

# set update scheduler
schedule.every().day.at("09:15").do(do_auth_update)
schedule.every().day.at("12:45").do(do_auth_update)

while True:
    schedule.run_pending()
    time.sleep(30)
