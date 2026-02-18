from __future__ import annotations

import flask
import traceback

from humblePhlipperPython.schemata.api.next_command_request import NextCommandRequest
from humblePhlipperPython.schemata.api.report_events_request import ReportEventsRequest
from humblePhlipperPython.schemata.domain.event import Event, Label as EventLabel
from humblePhlipperPython.services.command_service import build_next_command  
from humblePhlipperPython.services.event_ingestion import ingest_reported_events

bp = flask.Blueprint("routes", __name__)

@bp.route("/getNextCommand", methods=["POST"])
def next_command() -> tuple[flask.Response, int]:
    try:
        ncr = NextCommandRequest.model_validate(flask.request.get_json())                # receive request for command event (BID, ASK, CANCEL, etc.)
        command_event = build_next_command(ncr)                                          # update caches and generate command event
        return flask.jsonify(command_event.model_dump(mode="json", by_alias=True)), 200  # return command event
    except Exception as e:
        print(f"Error at /getNextCommand: {e}")
        traceback.print_exc()
        return flask.jsonify(Event(label=EventLabel.ERROR, text=str(e)).model_dump(mode="json", by_alias=True)), 500

@bp.route("/reportEvents", methods=["POST"])
def report_events() -> tuple[str, int]:
    try:
        rer = ReportEventsRequest.model_validate(flask.request.get_json())               # receive list of trade and polling state events
        ingest_reported_events(rer)                                                      # update 4-hour limits cache and events history
        return "", 204                                                                   # nothing to return
    except Exception as e:
        print(f"Error at /reportEvents: {e}")
        traceback.print_exc()
        return "", 500
