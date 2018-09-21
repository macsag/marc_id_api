from waitress import serve
from api_morepath import *

logging.root.addHandler(logging.StreamHandler(sys.stdout))
logging.root.setLevel(level=logging.DEBUG)


serve(App(), listen='*:80')