package humblePhlipperNet.controllers;

import humblePhlipperNet.models.Event;
import humblePhlipperNet.models.EventList;
import humblePhlipperNet.utils.OsrsConstants;

import java.awt.*;
import java.text.DecimalFormat;
import java.util.*;
import java.util.List;

public class Paint {
    private final long startTime = System.currentTimeMillis();
    private final DecimalFormat commaFormat = new DecimalFormat("#,###");
    private final Color recBg = new Color(0, 0, 0, 127);
    private double profit = 0;
    private EventList eventList = new EventList();
    private TreeMap<Long, Double> timeCumProfitMap = new TreeMap<>();
    private Map<Integer, SlotOverlay> slotOverlayMap = new HashMap<>();
    private List<Map.Entry<String, Double>> sortedItemNameProfitMap = new ArrayList<>();

    public Paint() {
        timeCumProfitMap.put(0L, 0.0);
    }

    public void onPaint(Graphics g) {
        drawChatOverlay(g); // runtime, config...
        plotProfit(g); // graph
        drawSlotOverlays(g); // profit notifications for sells
        drawInventoryOverlay(g); // profits by item
    }

    public void giveNewEventList(EventList newEventList) {
        for (int i = 0; i < OsrsConstants.NUM_GE_SLOTS; i++) {
            Event event = newEventList.get(i);
            if (event == null) { continue; }
            if (event.getLabel() != Event.Label.TRADE) { continue; }
            eventList.increment(event);
            double newProfit = eventList.getTotalProfit();
            timeCumProfitMap.put(System.currentTimeMillis() - startTime, newProfit);
            slotOverlayMap.put(i, new SlotOverlay(newProfit - profit, System.currentTimeMillis()));
            profit = newProfit;
        }
        sortedItemNameProfitMap = eventList.getSortedItemNameProfitList();
    }

    private String formatTime(long elapsedMillis) {
        long totalSeconds = elapsedMillis / 1000;
        long hours = totalSeconds / 3600;
        long minutes = (totalSeconds % 3600) / 60;
        long seconds = totalSeconds % 60;
        return String.format("%02d:%02d:%02d", hours, minutes, seconds);
    }

    private void drawChatOverlay(Graphics g) {
        long elapsedMillis = System.currentTimeMillis() - startTime;
        double profitPerHour = (3600000.0 * profit) / elapsedMillis;

        g.setColor(recBg);
        g.fillRect(7, 344, 506, 132);
        g.setColor(Color.WHITE);
        g.drawString("Profit: " + commaFormat.format(Math.round(profit)) + " (" + commaFormat.format(Math.round(profitPerHour)) + "/hr)", 13, 360);
        g.drawString("Runtime: " + formatTime(elapsedMillis), 13, 380);
        g.drawString("* Events output to console log", 13, 400);
        g.drawString("* Trade sell quantities are negative", 13, 420);
        g.drawString("* Trade sell prices are pre-tax", 13, 440);
        g.drawString("", 13, 460);
        g.drawString("", 200, 460);
        g.drawString("", 260, 360);
        g.drawString("", 260, 380);
        g.drawString("", 260, 400);
        g.drawString("", 260, 420);
        g.drawString("", 260, 440);
        g.drawString("", 260, 460);
    }

    private void plotProfit(Graphics g) {
        g.setColor(recBg);
        g.fillRect(547,345,190,120);
        g.setColor(Color.WHITE);

        g.drawLine(567, 445, 567+150,445); // x-axis
        g.drawLine(567, 445, 567,365); // y-axis

        if (timeCumProfitMap.size() < 2) { return; }

        Long minX = timeCumProfitMap.firstKey();
        Long maxX = timeCumProfitMap.lastKey();
        Double minY = timeCumProfitMap.values().stream().min(Double::compareTo).orElse(0.0);
        Double maxY = timeCumProfitMap.values().stream().max(Double::compareTo).orElse(0.0);

        if (maxY.equals(minY)) { return; }

        final double y0 = (0 - minY) * 80 / (maxY - minY);
        g.drawLine(567, (int) (445 - y0), 567 + 150, (int) (445 - y0)); // y = 0 line

        g.drawString(commaFormat.format(Math.round((double) maxX /60000)) + "m", 697, 460);
        g.drawString(commaFormat.format(Math.round(minY)), 547 + 10, 460);
        g.drawString(commaFormat.format(Math.round(maxY)), 547 + 10, 360);

        int prevX = 567;
        int prevY = (int) (445 - y0);
        for (Map.Entry<Long, Double> entry : timeCumProfitMap.entrySet()) {
            Long xValue = entry.getKey();
            Double yValue = entry.getValue();

            int x = (int) (567 + ((xValue - minX) * 150 / (maxX - minX)));
            int y = (int) (445 - ((yValue - minY) * 80 / (maxY - minY)));

            g.setColor(y < prevY ? Color.GREEN : Color.RED);
            g.drawLine(prevX, prevY, x, y);

            prevX = x;
            prevY = y;
        }
    }

    private void drawInventoryOverlay(Graphics g) {
        final int DISPLAY_LIMIT = 16; // Still useful for rendering constraints
        g.setColor(recBg);
        g.fillRect(547, 0, 190, 345);

        int size = sortedItemNameProfitMap.size();
        List<Map.Entry<String, Double>> itemNameProfitMapToDisplay = new ArrayList<>();

        if (size > DISPLAY_LIMIT) {
            itemNameProfitMapToDisplay.addAll(sortedItemNameProfitMap.subList(0, DISPLAY_LIMIT/2));
            itemNameProfitMapToDisplay.add(null);
            itemNameProfitMapToDisplay.addAll(sortedItemNameProfitMap.subList(size - 8, size));
        } else {
            itemNameProfitMapToDisplay.addAll(sortedItemNameProfitMap);
        }

        for (int i = 0; i < itemNameProfitMapToDisplay.size(); i++) {
            Map.Entry<String, Double> entry = itemNameProfitMapToDisplay.get(i);
            if (entry == null) {
                g.setColor(Color.WHITE);
                g.drawString("...", 567, 20 + i * 20);
                continue;
            }

            String formattedItemName = formatItemName(entry.getKey());
            String formattedProfit = formatProfit(entry.getValue());
            g.setColor(Color.WHITE);
            g.drawString(formattedItemName, 567, 20 + i * 20);
            g.setColor(entry.getValue() > 0 ? Color.GREEN : Color.RED);
            if (entry.getValue() == 0) { g.setColor(Color.WHITE); }
            g.drawString(formattedProfit, 697, 20 + i * 20);
        }
    }



    private void drawSlotOverlays(Graphics g) {
        long currentTime = System.currentTimeMillis();
        Iterator<Map.Entry<Integer, SlotOverlay>> iterator = slotOverlayMap.entrySet().iterator();
        while (iterator.hasNext()) {
            Map.Entry<Integer, SlotOverlay> entry = iterator.next();
            int slotIndex = entry.getKey();
            SlotOverlay overlay = entry.getValue();
            if (currentTime - overlay.timestamp > 1500) { iterator.remove();}
            double profit = overlay.deltaProfit;
            int x = 80 + (slotIndex % 4) * 120;
            int y = 150 + (slotIndex / 4) * 115;
            String formattedProfit = formatProfit(profit);
            g.setColor((profit > 0) ? Color.GREEN : (profit < 0) ? Color.RED : Color.WHITE);
            g.drawString(formattedProfit, x, y);
        }
    }

    private static String formatProfit(double profit) {
        if (profit == 0) { return "0"; }
        String sign = (profit > 0) ? "+" : (profit < 0) ? "-" : "";
        double absProfit = Math.abs(Math.round(profit));
        String formattedProfit;
        if (absProfit >= 1_000_000) {
            formattedProfit = String.format("%.1fm", absProfit / 1_000_000);
        } else if (absProfit >= 100_000) {
            formattedProfit = String.format("%.0fk", absProfit / 1000);
        } else if (absProfit >= 1000) {
            formattedProfit = String.format("%.1fk", absProfit / 1000);
        } else {
            formattedProfit = String.format("%.0f", absProfit);
        }
        return sign + formattedProfit;
    }

    private String formatItemName(String itemName) {
        final int MAX_LENGTH = 20;
        if (itemName.length() <= MAX_LENGTH) {
            return itemName;
        }

        int charsToShow = MAX_LENGTH - 3; //
        int frontChars = (int) Math.ceil(charsToShow / 2.0);
        int backChars = (int) Math.floor(charsToShow / 2.0);

        String front = itemName.substring(0, frontChars);
        String back = itemName.substring(itemName.length() - backChars);

        return front + "..." + back;
    }

    private static class SlotOverlay {
        double deltaProfit;
        long timestamp;

        SlotOverlay(double deltaProfit, long timestamp) {
            this.deltaProfit = deltaProfit;
            this.timestamp = timestamp;
        }
    }
}
