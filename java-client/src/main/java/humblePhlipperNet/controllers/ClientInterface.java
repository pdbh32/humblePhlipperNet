package humblePhlipperNet.controllers;

import humblePhlipperNet.models.InventoryItemList;
import humblePhlipperNet.models.OfferList;

import java.nio.file.Path;
import java.util.function.Consumer;

public interface ClientInterface {
    void log(Object o);
    void debug(Object o);
    boolean openGrandExchange();
    boolean cancel(int index);
    boolean collect();
    boolean bid(int itemId, int amount, int price);
    boolean ask(int itemId, int amount, int price);
    boolean bond();
    Runnable offerListPolling(Consumer<OfferList> onNewOfferList, Consumer<Boolean> onNewPollingState);
    InventoryItemList getInventoryItemList();
    String getUser();
    int getMembersDaysLeft();
    boolean isTradeRestricted();
}
