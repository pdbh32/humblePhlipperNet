package humblePhlipperNet.models;

import java.util.Set;

public class Portfolio {
    OfferList offerList;
    InventoryItemList inventoryItemList;

    public Portfolio() {
        this.offerList = new OfferList();
        this.inventoryItemList = new InventoryItemList();
    }
    public Portfolio(OfferList offerList, InventoryItemList inventoryItemList) {
        this.offerList = offerList;
        this.inventoryItemList = inventoryItemList;
    }

    public OfferList getOfferList() {
        return offerList;
    }

    public InventoryItemList getInventoryItemList() {
        return inventoryItemList;
    }

    public Set<Integer> getItemIdSet() {
        Set<Integer> itemIdSet = offerList.getItemIdSet();
        itemIdSet.addAll(inventoryItemList.getItemIdSet());
        return itemIdSet;
    }
    public boolean contains(int itemId) { return inventoryItemList.count(itemId) > 0 || offerList.contains(itemId); }

    public void setInventoryItemList(InventoryItemList inventoryItemList) { this.inventoryItemList = inventoryItemList; }
}
