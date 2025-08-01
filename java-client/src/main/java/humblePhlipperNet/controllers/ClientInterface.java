package humblePhlipperNet.controllers;

import humblePhlipperNet.models.Portfolio;

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
    int getMembersDaysLeft();
    boolean isTradeRestricted();
    Path getwd();
    String getUser();
    Runnable portfolioPolling(Consumer<Portfolio> onNewPortfolio);
}
