import platformdirs
import pathlib
import random

FLASK_SERVER_HOST = "0.0.0.0"
FLASK_SERVER_PORT = 5000
FLASK_SERVER_DEBUG = False
WIKI_REQUEST_HEADERS = {"User-Agent": "humblePhlipperNet"}
WIKI_REQUEST_OFFSET_SECONDS = random.randint(5,20)
MAX_BID_AGE_SECONDS = 60 # if an item in bidding_cache hasn't been updated in this many seconds, assume it's no longer being bid (bot is NLA)
MAX_BUCKETS = 12  # Maximum number of 5m/1h buckets to keep in the cache
AUTO_BOND_DAYS = -1 # Bond if the user has less than this many days of membership left and has a bond / can afford it (set to -1 to never bond)
DATA_DIR = pathlib.Path(platformdirs.user_data_dir("humblePhlipperNet", "apnasus"))