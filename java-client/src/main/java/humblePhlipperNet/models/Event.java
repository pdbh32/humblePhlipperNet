package humblePhlipperNet.models;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class Event {

    public enum Label {
        START_POLLING,
        END_POLLING,
        TRADE,
        BID,
        ASK,
        CANCEL,
        COLLECT,
        BOND,
        IDLE,
        ERROR,
    }

    private static final Gson GSON = new Gson();
    final long timestamp;
    final Label label;
    final Integer itemId;
    final String itemName;
    final Integer quantity;
    final Integer price;
    final Integer slotIndex;
    final String text;

    public Event(long timestamp, Label label, Integer itemId, String itemName, Integer quantity, Integer price, Integer slotIndex, String text) {
        this.timestamp = timestamp;
        this.label = label;
        this.itemId = itemId;
        this.itemName = itemName;
        this.quantity = quantity;
        this.price = price;
        this.slotIndex = slotIndex;
        this.text = text;
    }

    @Override
    public String toString() {
        return GSON.toJson(this);
    }

    public String toCSV() {
        return timestamp + "," + label + "," + itemId + "," + itemName + "," + quantity + "," + price + "," + slotIndex + "," + text;
    }

    public long getTimestamp() { return timestamp; }

    public Label getLabel() { return label; }

    public Integer getItemId() { return itemId; }

    public String getItemName() { return itemName; }

    public Integer getQuantity() { return quantity; }

    public Integer getPrice() { return price; }

    public Integer getSlotIndex() { return slotIndex; }

    public String getText() { return text; }
}
