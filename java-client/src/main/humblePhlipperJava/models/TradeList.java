package humblePhlipperJava.models;

import humblePhlipperJava.utils.Tax;
import org.dreambot.api.utilities.Logger;

import java.util.*;
import java.util.stream.Collectors;

public class TradeList extends ArrayList<TradeList.Trade> {

    public TradeList() {
        super();
    }

    public TradeList(int initialCapacity) {
        super(initialCapacity);
        for (int i = 0; i < initialCapacity; i++) {
            add(null);
        }
    }

    public TradeList(String csv) {
        String[] trades = csv.split("\\n");
        for (int i = 1; i < trades.length; i++) {
            add(Trade.fromCSV(trades[i]));
        }
    }

    public TradeList(TradeList other) {
        super(other.size());
        for (Trade trade : other) {
            if (trade == null) {
                this.add(null);
                continue;
            }
            this.add(new Trade(
                    trade.getTimestamp(),
                    trade.getItemId(),
                    trade.getItemName(),
                    trade.getQuantity(),
                    trade.getPrice()
            ));
        }
    }

    public String getCSV(boolean includeHeader) {
        StringBuilder csvBuilder = new StringBuilder();
        if(includeHeader) { csvBuilder.append("timestamp,itemId,itemName,quantity,price");}
        for (Trade trade : this) {
            if (trade == null) { continue; }
            csvBuilder.append("\n").append(trade.toCSV());
        }
        return csvBuilder.toString();
    }

    public void increment(Trade newTrade) {
        if (newTrade == null) { return; }
        add(newTrade);
    }
    public void increment(TradeList newTradeList) {
        for (Trade newTrade : newTradeList) {
            increment(newTrade);
        }
    }

    public Map<String, TradeList> splitByName() {
        Map<String, TradeList> tradeListMap = new HashMap<>();
        for (Trade trade : this) {
            if (trade == null) { continue; }
            tradeListMap.computeIfAbsent(trade.getItemName(), k -> new TradeList()).add(trade);
        }
        return tradeListMap;
    }

    private static double getItemSublistProfit(TradeList itemSublist) {
        Double avgBuyPrice = null;
        Double avgSellPrice = null;
        double inventory = 0;
        double profit = 0;
        for (Trade trade : itemSublist) {
            if (trade == null) { continue; }
            Logger.log(trade.toCSV());
            if (trade.getQuantity() > 0) { // buys are recorded as a positive quantity
                if (inventory < 0 & avgSellPrice != null) {
                    profit += (Tax.getPostTaxPrice(trade.getItemId(), avgSellPrice) - trade.getPrice()) * Math.min(trade.getQuantity(), -1 * inventory);
                }
                avgBuyPrice = avgBuyPrice == null ? trade.getPrice() : (trade.getQuantity() * trade.getPrice() + inventory * avgBuyPrice) / (trade.getQuantity() + inventory);
            } else if (trade.getQuantity() < 0) { // sells are recorded as a negative quantity
                if (inventory > 0 & avgBuyPrice != null) {
                    profit += (Tax.getPostTaxPrice(trade.getItemId(), trade.getPrice()) - avgBuyPrice) * Math.min(-1 * trade.getQuantity(), inventory);
                }
                avgSellPrice = avgSellPrice == null ? trade.getPrice() : (trade.getQuantity() * trade.getPrice() + inventory * avgSellPrice) / (trade.getQuantity() + inventory);
            }
            inventory += trade.getQuantity();
            if (inventory <= 0) { avgBuyPrice = null; }
            if (inventory >= 0) { avgSellPrice = null; }
        }
        return profit;
    }

    public Map<String, Double> getItemNameProfitMap() {
        Map<String, TradeList> itemSublistMap = splitByName();
        Map<String, Double> nameProfitMap = new HashMap<>();
        for (Map.Entry<String, TradeList> entry : itemSublistMap.entrySet()) {
            nameProfitMap.put(entry.getKey(), getItemSublistProfit(entry.getValue()));
        }
        return nameProfitMap;
    }

    public List<Map.Entry<String, Double>> getSortedItemNameProfitList() { // sort highest to lowest profit
        return getItemNameProfitMap().entrySet()
                .stream()
                .sorted(Map.Entry.<String, Double>comparingByValue(Comparator.reverseOrder())
                        .thenComparing(Map.Entry.comparingByKey())) // sort by item name for tie-breaking
                .collect(Collectors.toList());
    }

    public int getTotalProfit() {
        Map<String, Double> nameProfitMap = getItemNameProfitMap();
        return (int) nameProfitMap.values().stream().mapToDouble(Double::doubleValue).sum();
    }
    public final static class Trade {
        final long timestamp;
        final int itemId;
        final String itemName;
        final int quantity;
        final double price;

        public Trade(long timestamp, int itemId, String itemName, int quantity, double price) {
            this.timestamp = timestamp;
            this.itemId = itemId;
            this.itemName = itemName;
            this.quantity = quantity;
            this.price = price;
        }

        public static Trade fromCSV(String CSV) {
            String[] values = CSV.split(",");
            return new Trade(Long.parseLong(values[0]),
                    Integer.parseInt(values[1]),
                    values[2],
                    Integer.parseInt(values[3]),
                    Double.parseDouble(values[4]));
        }

        public String toCSV() { return timestamp + "," + itemId + "," + itemName + "," + quantity + "," + price; }

        public long getTimestamp() { return timestamp; }

        public int getItemId() { return itemId; }

        public String getItemName() { return itemName; }

        public Integer getQuantity() { return quantity; }

        public Double getPrice() { return price; }
    }

}
