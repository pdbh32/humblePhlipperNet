//Session.java

package humblePhlipperNet.controllers;

import com.google.gson.Gson;
import humblePhlipperNet.models.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

import static java.lang.Thread.sleep;

public class Session {
    private static final Gson gson = new Gson();
    private static final Logger log = LoggerFactory.getLogger(Session.class);

    ClientInterface ci;
    Long sessionTimestamp; // = System.currentTimeMillis();
    public Paint paint;
    EventList eventList;
    OfferList offerList;
    Event.Label lastCommandLabel;
    boolean lastPollingState;
    Thread offerListPollingThread;

    public Session(ClientInterface ci) { init(ci); }
    public Session(ClientInterface ci, String... params) { init(ci); }

    private void init(ClientInterface ci) {
        this.ci = ci;
        this.sessionTimestamp = Instant.now().toEpochMilli();
        this.paint = new Paint(); // simple graphics
        this.eventList = new EventList(); // a list of events made during this session
        this.offerList = new OfferList();
        this.lastCommandLabel = null; // to keep track of if lastCommandLabel was IDLE and avoid spamming requests
        this.lastPollingState = false;
        this.offerListPollingThread = new Thread(ci.offerListPolling(newOfferListConsumer(), newPollingStateConsumer())); // we poll offerList to get more accurate timestamps
        this.offerListPollingThread.start();
    }

    public void onLoop() {
        NextCommandRequest request = new NextCommandRequest(this.offerList, this.ci.getInventoryItemList(), this.ci.getUser(), this.ci.getMembersDaysLeft(), this.ci.isTradeRestricted());
        this.ci.debug(gson.toJson(request));
        Event command = Network.getNextCommand(request);
        this.ci.log(command);

        this.ci.openGrandExchange();

        switch (command.getLabel()) {
            case CANCEL:
                this.ci.cancel(command.getSlotIndex());
                break;
            case COLLECT:
                this.ci.collect();
                break;
            case ASK:
                this.ci.ask(command.getItemId(), command.getQuantity(), command.getPrice());
                break;
            case BID:
                this.ci.bid(command.getItemId(), command.getQuantity(), command.getPrice());
                break;
            case BOND:
                this.ci.bond();
                break;
            case IDLE:
                break;
            case ERROR:
                this.ci.log(command.getText());
                break;
        }

        try {
            sleep(getSleepMs(command.getLabel()));
            lastCommandLabel = command.getLabel();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private long getSleepMs(Event.Label commandLabel) {
        if (Event.Label.IDLE.equals(commandLabel)) {
            return ThreadLocalRandom.current().nextLong(10_000, 60_001);
        }
        return ThreadLocalRandom.current().nextLong(1_000, 5_001);
    }

    public void onExit() {
        this.offerListPollingThread.interrupt();
        ci.log(this.eventList.getCSV(true));
        ci.log("Total Profit: " + this.eventList.getTotalProfit());
    }

    public Consumer<OfferList> newOfferListConsumer() { return this::onNewOfferList; }

    private void onNewOfferList(OfferList newOfferList) {
        if (newOfferList == null || newOfferList.getClass() != OfferList.class) { return; }
        EventList newTradeList = this.offerList.update(newOfferList);
        if (newTradeList.allNull()) {  return; }
        for (Event event : newTradeList) { if (event != null) { this.ci.log(event); } }
        this.eventList.increment(newTradeList);
        this.paint.giveNewEventList(newTradeList);
        Network.reportEvents(new ReportEventsRequest(newTradeList, this.ci.getUser()));
    }

    public Consumer<Boolean> newPollingStateConsumer() { return this::onNewPollingState; }

    private void onNewPollingState(Boolean isPolling) {
        if (isPolling != lastPollingState) {
            Event newEvent = new Event(Instant.now().getEpochSecond(), isPolling ? Event.Label.START_POLLING : Event.Label.END_POLLING, null, null, null, null, null, null);
            this.ci.log(newEvent);
            this.eventList.increment(newEvent);
            EventList newEventList = new EventList();
            newEventList.increment(newEvent);
            Network.reportEvents(new ReportEventsRequest(newEventList, this.ci.getUser()));
            lastPollingState = isPolling;
        }
    }

}
