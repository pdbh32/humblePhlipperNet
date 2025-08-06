import requests
import config
import trades_cache

BLUE = 5814783

def send():
    if not config.DISCORD_WEBHOOK_URL: return

    statistics = _make_statistics()

    data = {
        "content":  f"Total Profit: {statistics['Total Profit']:,}",
        "username": "humblePhlipper",
        "avatar_url": "https://i.postimg.cc/W4DLDmhP/humble-Phlipper.png",
        "tts": False,
        "embeds": [
            {
                "title": "Statistics",
                "fields": [
                    {"name": "Contributing Instances", "value": str(statistics['Contributing Instances']), "inline": False},
                    {"name": "Total Profit", "value": f"{statistics['Total Profit']:,}", "inline": False},
                    {"name": "Total Runtime (Hours)", "value": f"{statistics['Total Runtime (Hours)']:.1f}", "inline": False}
                ],
                "color": BLUE
            }
        ]
    }
    
    requests.post(config.DISCORD_WEBHOOK_URL, json=data)

def _make_statistics():
    user_to_tradeList = trades_cache.get()

    user_to_statistics = {
        user: {
            'profit': tradeList.get_total_profit(),
            'runtime': tradeList[-1].timestamp - tradeList[0].timestamp

        }
        for user, tradeList in user_to_tradeList.items() if len(tradeList) > 0
    }

    statistics = {
        'Contributing Instances': len(user_to_statistics),
        'Total Profit': sum(stat['profit'] for stat in user_to_statistics.values()),
        'Total Runtime (Hours)': sum(stat['runtime'] for stat in user_to_statistics.values()) / 3600
    }

    return statistics
