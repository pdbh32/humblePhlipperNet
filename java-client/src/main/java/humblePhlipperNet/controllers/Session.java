//Session.java

package humblePhlipperNet.controllers;

import com.google.gson.Gson;
import humblePhlipperNet.models.*;

import java.time.Instant;
import java.util.function.Consumer;

import static java.lang.Thread.sleep;

public class Session {
    private static final Gson gson = new Gson();

    ClientInterface ci;
    Long sessionTimestamp; // = System.currentTimeMillis();
    public Paint paint;
    TradeList tradeList;
    Portfolio portfolio;
    ActionData.Action lastAction;
    Thread portfolioPollingThread;

    public Session(ClientInterface ci) { init(ci); }
    public Session(ClientInterface ci, String... params) { init(ci); }

    private void init(ClientInterface ci) {
        this.ci = ci;
        this.sessionTimestamp = Instant.now().toEpochMilli();
        this.paint = new Paint(); // simple graphics
        this.tradeList = new TradeList(); // a list of trades made during this session
        this.portfolio = new Portfolio(); // consists of InventoryItemList and (GE) OfferList
        this.lastAction = null; // to keep track of if lastAction was IDLE and avoid spamming requests
        this.portfolioPollingThread = new Thread(ci.portfolioPolling(newPortfolioConsumer())); // regularly update this.portfolio
        this.portfolioPollingThread.start();
    }

    public void onLoop() {
        this.ci.debug(gson.toJson(new ActionRequest(this.portfolio, this.ci.getUser(), this.ci.getMembersDaysLeft(), this.ci.isTradeRestricted())));
        ActionData actionData = Network.requestActionData(this.portfolio, this.ci.getUser(), this.ci.getMembersDaysLeft(), this.ci.isTradeRestricted());

        this.ci.openGrandExchange();

        switch (actionData.getAction()) {
            case CANCEL:
                this.ci.log(actionData.getAction() + " " + actionData.getSlotIndex());
                this.ci.cancel(actionData.getSlotIndex());
                break;
            case COLLECT:
                this.ci.log(actionData.getAction() + " " + actionData.getSlotIndex());
                this.ci.collect();
                break;
            case ASK:
                this.ci.log(actionData.getAction() + " " + actionData.getItemId() + " " + actionData.getQuantity() + " " + actionData.getPrice());
                this.ci.ask(actionData.getItemId(), actionData.getQuantity(), actionData.getPrice());
                break;
            case BID:
                this.ci.log(actionData.getAction() + " " + actionData.getItemId() + " " + actionData.getQuantity() + " " + actionData.getPrice());
                this.ci.bid(actionData.getItemId(), actionData.getQuantity(), actionData.getPrice());
                break;
            case BOND:
                this.ci.log(actionData.getAction());
                this.ci.bond();
                break;
            case IDLE:
                if (!ActionData.Action.IDLE.equals(this.lastAction)) { this.ci.log(actionData.getAction()); }
                break;
            case ERROR:
                this.ci.log(actionData.getAction() + " " + actionData.getText());
                break;
        }

        try {
            sleep(ActionData.Action.IDLE.equals(actionData.getAction()) ? 5000 : 1500);
            lastAction = actionData.getAction();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public void onExit() {
        this.portfolioPollingThread.interrupt();
        ci.log(tradeList.getCSV(true));
        ci.log("Total Profit: " + tradeList.getTotalProfit());
    }

    public Consumer<Portfolio> newPortfolioConsumer() { return this::onNewPortfolio; }

    private void onNewPortfolio(Portfolio newPortfolio) {
        if (newPortfolio == null || newPortfolio.getClass() != Portfolio.class) { return; }
        this.portfolio.setInventoryItemList(newPortfolio.getInventoryItemList()); // update Portfolio InventoryItemList
        TradeList newTradeList = portfolio.getOfferList().update(newPortfolio.getOfferList()); // update Portfolio OfferList, and infer new trades by comparing old OfferList with new OfferList
        if (!newTradeList.getCSV(false).contains("\n")) { return; } // if no new trades, nothing to do
        ci.log(newTradeList.getCSV(false));
        this.tradeList.increment(newTradeList);
        this.paint.giveNewTradeList(newTradeList);
        Network.sendNewTradeList(newTradeList, this.ci.getUser());
    }

}
