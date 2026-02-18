package humblePhlipperNet.models;

public class NextCommandRequest {
    OfferList offerList;
    InventoryItemList inventoryItemList;
    String user;
    int membersDaysLeft;
    boolean tradeRestricted;

    public NextCommandRequest(OfferList offerList, InventoryItemList inventoryItemList, String user, int membersDaysLeft, boolean tradeRestricted) {
        this.offerList = offerList;
        this.inventoryItemList = inventoryItemList;
        this.user = user;
        this.membersDaysLeft = membersDaysLeft;
        this.tradeRestricted = tradeRestricted;
    }
}
