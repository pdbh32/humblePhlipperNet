package humblePhlipperJava.dreambot;

import humblePhlipperJava.controllers.ClientInterface;

import humblePhlipperJava.models.*;
import org.dreambot.api.Client;
import org.dreambot.api.methods.bond.Bond;
import org.dreambot.api.methods.container.impl.Inventory;
import org.dreambot.api.methods.grandexchange.GrandExchange;
import org.dreambot.api.methods.grandexchange.GrandExchangeItem;
import org.dreambot.api.methods.grandexchange.Status;
import org.dreambot.api.methods.quest.Quests;
import org.dreambot.api.methods.settings.PlayerSettings;
import org.dreambot.api.methods.settings.Varcs;
import org.dreambot.api.methods.skills.Skills;
import org.dreambot.api.utilities.AccountManager;
import org.dreambot.api.utilities.Logger;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Objects;
import java.util.function.Consumer;
import java.util.stream.Collectors;

public class DreamBot implements ClientInterface {
    private final static int POLLING_INTERVAL_MS = 500; // milliseconds
    @Override
    public void log(Object o) {
        Logger.log(o);
    }
    @Override
    public void debug(Object o) {
        Logger.debug(o);
    }
    @Override
    public boolean openGrandExchange() { return (GrandExchange.isOpen() && GrandExchange.goBack()) || GrandExchange.open(); }
    @Override
    public boolean cancel(int index) { return GrandExchange.cancelOffer(index); }
    @Override
    public boolean collect() { return GrandExchange.collect(); }
    @Override
    public boolean ask(int itemId, int amount, int price) { return GrandExchange.sellItem(itemId, amount, price); }
    @Override
    public boolean bid(int itemId, int amount, int price) { return GrandExchange.buyItem(itemId, amount, price); }
    @Override
    public boolean bond() { return Bond.redeem(1)); }
    @Override
    public int getMembersDaysLeft() { return PlayerSettings.getConfig(1780); }
    @Override
    public boolean isTradeRestricted() {
        if (getMembersDaysLeft() > 0) return false;

        int qp = Quests.getQuestPoints();
        int total = Skills.getTotalLevel();
        int minutes = Varcs.getInt(526);

        return qp < 10 || total < 100 || minutes < 1200;
    }
    @Override
    public Path getwd() { return Paths.get(System.getProperty("user.dir"),"Scripts", "humblePhlipperJava"); }
    @Override
    public String getUser() {return AccountManager.getAccountUsername();}
    @Override
    public Runnable portfolioPolling(Consumer<Portfolio> onNewPortfolio) {
        return () -> {
            while (!Thread.currentThread().isInterrupted()) {
                if (
                        Client.isLoggedIn() && !Client.getInstance().getRandomManager().isSolving() &&
                                Client.getInstance().getScriptManager().isRunning()
                ) {
                    onNewPortfolio.accept(new Portfolio(getOfferList(), getInventoryItemList()));
                }
                try {
                    Thread.sleep(POLLING_INTERVAL_MS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }

        };
    }
    public InventoryItemList getInventoryItemList() {
        return Inventory.all().stream()
                .filter(Objects::nonNull)
                .map(item -> new InventoryItemList.InventoryItem(item.getUnnotedItemID(), item.getAmount()))
                .collect(Collectors.toCollection(InventoryItemList::new));
    }

    public OfferList getOfferList() {
        return Arrays.stream(GrandExchange.getItems())
                .collect(OfferList::new, (offerList, item) -> offerList.set(item.getSlot(), getOffer(item)), (a, b) -> {});
    }

    /**
     * Offer corresponding to DreamBot's GrandExchangeItem.
     *
     * @param item GrandExchangeItem
     * @return slotIndex, ID, name, vol, price, transferredVol, transferredValue, status, readyToCollect
     */
    public OfferList.Offer getOffer(GrandExchangeItem item) {
        return new OfferList.Offer(
                item.getSlot(),
                (item.getID() == 0) ? -1 : item.getID(),
                item.getName(),
                item.getAmount(),
                item.getPrice(),
                item.getTransferredAmount(),
                item.getTransferredValue(),
                getGrandExchangeItemStatus(item.getStatus()),
                item.isReadyToCollect()
        );
    }
    /**
     * OffserStatus corresponding to DreamBot's GrandExchangeItem.Status
     *
     * @param status BUY, BUY_COLLECT, SELL, SELL_COLLECT, EMPTY
     * @return BUY, SELL, EMPTY
     */
    public OfferList.OfferStatus getGrandExchangeItemStatus(Status status) {
        if (status == null) { return null; }
        switch (status) {
            case BUY:
            case BUY_COLLECT:
                return OfferList.OfferStatus.BUY;
            case SELL:
            case SELL_COLLECT:
                return OfferList.OfferStatus.SELL;
            case EMPTY:
                return OfferList.OfferStatus.EMPTY;
            default:
                return null;
        }
    }
}

