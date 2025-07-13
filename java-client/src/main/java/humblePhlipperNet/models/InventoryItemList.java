package humblePhlipperNet.models;

import humblePhlipperNet.utils.OsrsConstants;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public class InventoryItemList extends ArrayList<InventoryItemList.InventoryItem> {

    public InventoryItemList() {
        super();
    }

    public final static class InventoryItem {
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

    public Set<Integer> getItemIdSet() {
        Set<Integer> itemIdSet = new HashSet<>();
        for (InventoryItem item : this) {
            itemIdSet.add(item.itemId);
        }
        return itemIdSet;
    }

    public int count(int itemId) {
        int count = 0;
        for (InventoryItem item : this) {
            if (item.itemId == itemId) {
                count += item.quantity;
            }
        }
        return count;
    }

    public Long getCash() {
        long cash  = 0L;
        for (InventoryItemList.InventoryItem inventoryItem : this) {
            if (inventoryItem.getItemId() == OsrsConstants.COINS_ID) {
                cash += inventoryItem.getQuantity();
            }
        }
        return cash;
    }
}
