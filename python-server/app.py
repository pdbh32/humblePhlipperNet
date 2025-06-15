import flask
import logic 
import config

app = flask.Flask(__name__)

@app.route('/getActionData', methods=['POST'])
def decision_endpoint():
    data = flask.request.get_json()
    try:
        action_data = logic.getActionData(data)
        return flask.jsonify(action_data), 200
    except Exception as e:
        print(f"Error processing action data: {e}")
        return flask.jsonify({"action": "ERROR", "text": str(e)}), 500

@app.route('/sendTradeList', methods=['POST'])
def receive_trade_list():
    data = flask.request.get_json()
    try:
        logic.update_four_limits(data)
        return '', 204  # No Content
    except Exception as e:
        print(f"Error processing trade list: {e}")
        return '', 500

if __name__ == "__main__":
    app.run(host=config.FLASK_SERVER_HOST, port=config.FLASK_SERVER_PORT, debug=config.FLASK_SERVER_DEBUG, threaded=True)

