import flask
import traceback

import logic 
import config
import four_hour_limits
import models
import wiki_cache
import statistics_cache
import scheduler

app = flask.Flask(__name__)

@app.route('/getActionData', methods=['POST'])
def decision_endpoint():
    try:
        payload = models.ActionRequest(**flask.request.get_json())
        action_data = logic.getActionData(payload)
        return flask.jsonify(action_data.dict()), 200
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return flask.jsonify({"action": "ERROR", "text": str(e)}), 500

@app.route('/sendTradeList', methods=['POST'])
def receive_trade_list():
    data = flask.request.get_json()
    try:
        limits = four_hour_limits.FourHourLimits(data["user"])
        limits.update_with_trades(data["tradeList"])
        return '', 204  # No Content
    except Exception as e:
        print(f"Error processing trade list: {e}")
        return '', 500

if __name__ == "__main__":
    wiki_cache.init()
    statistics_cache.init()
    scheduler.init()
    app.run(host=config.FLASK_SERVER_HOST, port=config.FLASK_SERVER_PORT, debug=config.FLASK_SERVER_DEBUG, threaded=True)

