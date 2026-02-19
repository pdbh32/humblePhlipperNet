package humblePhlipperNet.controllers;

import com.google.gson.Gson;
import humblePhlipperNet.models.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

import static java.lang.Thread.sleep;

public class Session {
    private static final Gson gson = new Gson();

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
        this.offerList = this.loadOfferList();
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
        this.saveOfferList();
        this.ci.log(this.eventList.getCSV(true));
        this.ci.log("Total Profit: " + this.eventList.getTotalProfit());
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

    private OfferList loadOfferList() {
        Path p = offerListPath();
        try {
            return Files.exists(p) ? gson.fromJson(Files.readString(p), OfferList.class) : new OfferList(true);
        } catch (IOException e) {
            ci.log(e);
            return new OfferList(true);
        }
    }

    private void saveOfferList() {
        Path p = offerListPath();
        try {
            Files.createDirectories(p.getParent());
            Files.writeString(p, gson.toJson(this.offerList));
        } catch (IOException e) {
            ci.log(e);
        }
    }

    private Path offerListPath() {
        String userFile = this.ci.getUser().replaceAll("[<>:\"/\\\\|?*\\x00-\\x1F]", "").trim().replaceAll("\\.+$", "") + ".json";
        return this.ci.getWd().resolve("offerLists").resolve(userFile);
    }

}
