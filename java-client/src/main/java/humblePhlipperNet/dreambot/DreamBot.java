package humblePhlipperNet.dreambot;

import humblePhlipperNet.controllers.ClientInterface;

import humblePhlipperNet.models.*;
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
import org.dreambot.api.randoms.LoginSolver;
import org.dreambot.api.randoms.WelcomeScreenSolver;
import org.dreambot.api.utilities.AccountManager;
import org.dreambot.api.utilities.Logger;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Objects;
import java.util.function.Consumer;
import java.util.stream.Collectors;

public class DreamBot implements ClientInterface {
    private final static int POLLING_INTERVAL_MS = 1; // milliseconds

    @Override
    public void log(Object o) { Logger.log(o); }

    @Override
    public void debug(Object o) { Logger.debug(o); }

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
    public boolean bond() { return Bond.redeem(1); }

     @Override
    public String getUser() {return AccountManager.getAccountUsername();}

    @Override
    public Runnable offerListPolling(Consumer<OfferList> onNewOfferList, Consumer<Boolean> onNewPollingState) {
        return () -> {
            while (!Thread.currentThread().isInterrupted()) {
                if (
                        Client.getInstance().getScriptManager().isRunning()
                        && Client.isLoggedIn()
                        && !(Client.getInstance().getRandomManager().isSolving() && (
                               Client.getInstance().getRandomManager().getCurrentSolver() instanceof WelcomeScreenSolver
                            || Client.getInstance().getRandomManager().getCurrentSolver() instanceof LoginSolver
                        ))
                ) {
                    onNewPollingState.accept(true);
                    onNewOfferList.accept(getOfferList());
                } else {
                    onNewPollingState.accept(false);
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

    @Override
    public InventoryItemList getInventoryItemList() {
        return Inventory.all().stream()
                .filter(Objects::nonNull)
                .map(item -> new InventoryItem(item.getUnnotedItemID(), item.getAmount()))
                .collect(Collectors.toCollection(InventoryItemList::new));
    }

    @Override
    public int getMembersDaysLeft() { return PlayerSettings.getConfig(1780); }

    @Override
    public boolean isTradeRestricted() {
        if (getMembersDaysLeft() > 0) return false;

        int qp = Quests.getQuestPoints();
        int total = Skills.getTotalLevel();
        int minutes = Varcs.getInt(526);

        return false; // qp < 10 || total < 100 || minutes < 1200; // minutes = Varcs.getInt(526) doesn't work so hardcode return for now
    }

    private OfferList getOfferList() {
        return Arrays.stream(GrandExchange.getItems())
                .collect(() -> new OfferList(true), (offerList, item) -> offerList.set(item.getSlot(), getOffer(item)), (a, b) -> {});
    }

    private Offer getOffer(GrandExchangeItem item) {
        return new Offer(
                (item.getID() == 0) ? -1 : item.getID(),
                item.getName(),
                item.getAmount(),
                item.getPrice(),
                item.getSlot(),
                item.getTransferredAmount(),
                item.getTransferredValue(),
                getGrandExchangeItemStatus(item.getStatus()),
                item.isReadyToCollect()
        );
    }
    
    private Offer.Status getGrandExchangeItemStatus(Status status) {
        if (status == null) { return null; }
        switch (status) {
            case BUY:
            case BUY_COLLECT:
                return Offer.Status.BUY;
            case SELL:
            case SELL_COLLECT:
                return Offer.Status.SELL;
            case EMPTY:
                return Offer.Status.EMPTY;
            default:
                return null;
        }
    }
    @Override
    public Path getWd() { return Paths.get(System.getProperty("user.dir"), "Scripts", "humblePhlipperNet"); }

}
