import schedule
import requests
import time
from base_url_config import BASE_URL
import functools

def catch_exceptions(job_func, cancel_on_failure=False):
    @functools.wraps(job_func)
    def wrapper(*args, **kwargs):
        try:
            return job_func(*args, **kwargs)
        except:
            import traceback
            print(traceback.format_exc())
            if cancel_on_failure:
                return schedule.CancelJob
    return wrapper

@catch_exceptions
def do_auth_update():
    requests.get('http://{}/update/authorities'.format(BASE_URL))

@catch_exceptions
def do_bib_update():
    requests.get('http://{}/update/bibs'.format(BASE_URL))

# set update scheduler
schedule.every().day.at("22:46").do(do_auth_update)
schedule.every().day.at("10:30").do(do_bib_update)

while True:
    schedule.run_pending()
    time.sleep(30)
