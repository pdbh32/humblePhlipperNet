package humblePhlipperNet.models;

import humblePhlipperNet.utils.Tax;

import java.util.*;
import java.util.stream.Collectors;

public class EventList extends ArrayList<Event> {

    public EventList() {
        super();
    }

    public EventList(int initialCapacity) {
        super(initialCapacity);
        for (int i = 0; i < initialCapacity; i++) {
            add(null);
        }
    }

    public boolean allNull() {
        return this.stream().allMatch(Objects::isNull);
    }

    public String getCSV(boolean includeHeader) {
        StringBuilder csvBuilder = new StringBuilder();
        if(includeHeader) { csvBuilder.append("timestamp,label,itemId,itemName,quantity,price,slotIndex,text");}
        for (Event event : this) {
            if (event == null) { continue; }
            csvBuilder.append("\n").append(event.toCSV());
        }
        return csvBuilder.toString();
    }

    public void increment(Event newEvent) {
        if (newEvent == null) { return; }
        add(newEvent);
    }
    public void increment(EventList newEventList) {
        for (Event newEvent : newEventList) {
            increment(newEvent);
        }
    }

    public Map<String, EventList> splitByName() {
        Map<String, EventList> eventListMap = new HashMap<>();
        for (Event event : this) {
            if (event == null) { continue; }
            eventListMap.computeIfAbsent(event.getItemName(), k -> new EventList()).add(event);
        }
        return eventListMap;
    }

    private static double getItemSublistProfit(EventList itemSublist) {
        Integer avgBuyPrice = null;
        Integer avgSellPrice = null;
        int inventory = 0;
        int profit = 0;
        for (Event event : itemSublist) {
            if (event == null || event.getLabel() != Event.Label.TRADE) { continue; }
            if (event.getQuantity() > 0) { // buys are recorded as a positive quantity
                if (inventory < 0 & avgSellPrice != null) {
                    profit += (Tax.getPostTaxPrice(avgSellPrice, event.getItemId()) - event.getPrice()) * Math.min(event.getQuantity(), -1 * inventory);
                }
                avgBuyPrice = avgBuyPrice == null ? event.getPrice() : (event.getQuantity() * event.getPrice() + inventory * avgBuyPrice) / (event.getQuantity() + inventory);
            } else if (event.getQuantity() < 0) { // sells are recorded as a negative quantity
                if (inventory > 0 & avgBuyPrice != null) {
                    profit += (Tax.getPostTaxPrice(event.getPrice(), event.getItemId()) - avgBuyPrice) * Math.min(-1 * event.getQuantity(), inventory);
                }
                avgSellPrice = avgSellPrice == null ? event.getPrice() : (event.getQuantity() * event.getPrice() + inventory * avgSellPrice) / (event.getQuantity() + inventory);
            }
            inventory += event.getQuantity();
            if (inventory <= 0) { avgBuyPrice = null; }
            if (inventory >= 0) { avgSellPrice = null; }
        }
        return profit;
    }

    public Map<String, Double> getItemNameProfitMap() {
        Map<String, EventList> itemSublistMap = splitByName();
        Map<String, Double> nameProfitMap = new HashMap<>();
        for (Map.Entry<String, EventList> entry : itemSublistMap.entrySet()) {
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

}
