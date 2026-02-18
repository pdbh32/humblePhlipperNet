package humblePhlipperNet.models;

import humblePhlipperNet.utils.OsrsConstants;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public class OfferList extends ArrayList<Offer> {
    public OfferList() {
        super(OsrsConstants.NUM_GE_SLOTS);
        for (int i = 0; i < OsrsConstants.NUM_GE_SLOTS; i++) { add(new Offer(i)); }
    }

    public Set<Integer> getItemIdSet() {
        Set<Integer> itemIdSet = new HashSet<>();
        for (Offer offer : this) {
            itemIdSet.add(offer.itemId);
        }
        return itemIdSet;
    }

    public boolean contains(int itemId) {
        for (Offer offer : this) {
            if (offer.itemId == itemId) { return true; }
        }
        return false;
    }

    @Override
    public String toString() {
        String s = "[";
        for (Offer offer : this) {
            s += offer.itemName + ", ";
        }
        return s += "]";
    }

    public EventList update(OfferList newOfferList) {
        if (newOfferList.size() != OsrsConstants.NUM_GE_SLOTS) {
            throw new IllegalArgumentException("newSlotList must have " + OsrsConstants.NUM_GE_SLOTS + " slots");
        }

        EventList tradeList = new EventList(OsrsConstants.NUM_GE_SLOTS);
        for (int i = 0; i < OsrsConstants.NUM_GE_SLOTS; i++) {
            Offer oldOffer = get(i);
            Offer newOffer = newOfferList.get(i);
            if (newOffer == null || newOffer.status == null) {
                newOffer = oldOffer;
            }
            this.set(i, newOffer);
            Event trade = newOffer.inferTrade(oldOffer);
            tradeList.set(i, trade);
        }
        return tradeList;
    }
}
