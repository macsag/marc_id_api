import schedule
import requests
import time
from base_url_config import BASE_URL

def do_auth_update():
    requests.get('http://{}/update/authorities'.format(BASE_URL))


# set update scheduler
schedule.every().day.at("17:26").do(do_auth_update)

while True:
    schedule.run_pending()
    time.sleep(1)