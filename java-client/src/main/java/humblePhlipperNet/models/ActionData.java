package humblePhlipperNet.models;

public class ActionData {
    private final Action action;
    private final Integer itemId;
    private final Integer quantity;
    private final Integer price;
    private final Integer slotIndex;
    private final String text;

    public ActionData(Action action, Integer itemId, Integer quantity, Integer price, Integer slotIndex, String text) {
        this.action = action;
        this.itemId = itemId;
        this.quantity = quantity;
        this.price = price;
        this.slotIndex = slotIndex;
        this.text = text;
    }

    public Action getAction() {
        return action;
    }

    public Integer getItemId() {
        return itemId;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public Integer getPrice() {
        return price;
    }

    public Integer getSlotIndex() {
        return slotIndex;
    }

    public String getText() { return text; }

    public enum Action {
        BID,
        ASK,
        CANCEL,
        COLLECT,
        BOND,
        IDLE,
        ERROR
    }
}
