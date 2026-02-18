package humblePhlipperNet.models;

public class ReportEventsRequest {
    EventList eventList;
    String user;

    public ReportEventsRequest(EventList eventList, String user) {
        this.eventList = eventList;
        this.user = user;
    }
}
