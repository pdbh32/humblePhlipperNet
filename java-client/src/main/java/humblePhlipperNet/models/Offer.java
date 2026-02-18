package humblePhlipperNet.models;

import java.time.Instant;

public class Offer {
    final public int itemId;
    final String itemName;
    public final int quantity;
    final public int price;
    final public int slotIndex;
    final int transferredQuantity;
    final int transferredValue;
    final boolean readyToCollect;
    final public Status status;

    public Offer(int index) {
        this.itemId = -1;
        this.itemName = null;
        this.quantity = 0;
        this.price = 0;
        this.slotIndex = index;
        this.transferredQuantity = 0;
        this.transferredValue = 0;
        this.status = null;
        this.readyToCollect = false;
    }

    public Offer(int itemId, String itemName, int quantity, int price, int slotIndex, int transferredQuantity,
                 int transferredValue, Status status, boolean readyToCollect) {
        this.itemId = itemId;
        this.itemName = itemName;
        this.quantity = quantity;
        this.price = price;
        this.slotIndex = slotIndex;
        this.transferredQuantity = transferredQuantity;
        this.transferredValue = transferredValue;
        this.status = status;
        this.readyToCollect = readyToCollect;
    }

    public Event inferTrade(Offer oldSlot) {
        int quantity = this.transferredQuantity - oldSlot.transferredQuantity;
        if (quantity <= 0) return null;

        int price = (this.transferredValue - oldSlot.transferredValue) / quantity;

        if (this.status == Status.SELL) {
            quantity = -1 * quantity; // negative quantity indicates a sell
        }

        return new Event(
            Instant.now().getEpochSecond(),
            Event.Label.TRADE,
            this.itemId,
            this.itemName,
            quantity,
            price,
            this.slotIndex,
            null
        );
    }

    public enum Status {
        EMPTY,
        BUY,
        SELL
    }
}
