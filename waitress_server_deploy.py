from waitress import serve
from api_morepath import *

logging.root.addHandler(logging.StreamHandler(sys.stdout))
logging.root.addHandler(logging.FileHandler('log_marc_api.txt', encoding='utf-8'))
logging.root.setLevel(level=logging.INFO)


serve(App(), listen=BASE_URL)