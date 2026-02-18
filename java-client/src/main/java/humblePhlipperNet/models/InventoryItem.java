package humblePhlipperNet.models;

public class InventoryItem {
    private final int itemId; // unnoted ID
    private final int quantity;

    public InventoryItem(int itemId, int quantity) {
        this.itemId = itemId;
        this.quantity = quantity;
    }

    public int getItemId() {
        return itemId;
    }

    public int getQuantity() {
        return quantity;
    }
}
