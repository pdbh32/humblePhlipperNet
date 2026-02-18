import platformdirs
import pathlib

CORE_DIR = pathlib.Path(platformdirs.user_data_dir("humblePhlipperNet", "apnasus"))

MARKET_DATA_DIR = CORE_DIR / "market_data"
FOUR_HOUR_LIMITS_DIR = CORE_DIR / "four_hour_limits"
EVENTS_DIR = CORE_DIR / "events"