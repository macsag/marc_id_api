from waitress import serve
import api_morepath
import logging
import sys
from base_url_config import BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt="%H:%M:%S",
    stream=sys.stdout)

formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')

root_fh = logging.FileHandler('log_marc_api.log', encoding='utf-8')
root_fh.setLevel(logging.INFO)
root_fh.setFormatter(formatter)
logging.root.addHandler(root_fh)


serve(api_morepath.App(), listen=BASE_URL)