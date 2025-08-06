import platformdirs
import pathlib
import random

FLASK_SERVER_HOST = "0.0.0.0"
FLASK_SERVER_PORT = 5000
WIKI_REQ_HEADERS = {"User-Agent": "humblePhlipperNet"}
WIKI_REQ_OFFSET_SECS = random.randint(5,20)
MAX_BID_AGE_SECS = 60 # if an item in bidding_cache hasn't been updated in this many seconds, assume it's no longer being bid (bot is NLA)
T = 12  # Number of 5m/1h buckets to keep in the cache and use in constructing time series statistics
AUTO_BOND_DAYS = 1 # Bond if the user has less than this many days of membership left and has a bond / can afford it (set to -1 to never bond)
DATA_DIR = pathlib.Path(platformdirs.user_data_dir("humblePhlipperNet", "apnasus"))
DISCORD_WEBHOOK_URL = None # Set to a Discord webhook URL to enable Discord notifications