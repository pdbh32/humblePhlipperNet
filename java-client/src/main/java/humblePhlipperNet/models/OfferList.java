package humblePhlipperNet.models;

import humblePhlipperNet.utils.OsrsConstants;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public class OfferList extends ArrayList<OfferList.Offer> {
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

    public Offer getByItemId(int itemId) {
        for (Offer offer : this) {
            if (offer.itemId == itemId) { return offer; }
        }
        return null;
    }

    public boolean isFull() {
        if (this.size() < OsrsConstants.NUM_GE_SLOTS) { return false; }
        for (Offer offer : this) {
            if (offer.status == null || offer.status == OfferStatus.EMPTY) { return false; }
        }
        return true;
    }

    @Override
    public String toString() {
        String s = "[";
        for (Offer offer : this) {
            s += offer.itemName + ", ";
        }
        return s += "]";
    }

    public TradeList update(OfferList newOfferList) {
        if (newOfferList.size() != OsrsConstants.NUM_GE_SLOTS) {
            throw new IllegalArgumentException("newSlotList must have " + OsrsConstants.NUM_GE_SLOTS + " slots");
        }

        TradeList tradeList = new TradeList(OsrsConstants.NUM_GE_SLOTS);
        for (int i = 0; i < OsrsConstants.NUM_GE_SLOTS; i++) {
            OfferList.Offer oldOffer = get(i);
            Offer newOffer = newOfferList.get(i);
            if (newOffer == null || newOffer.status == null) {
                newOffer = oldOffer;
            }
            this.set(i, newOffer);
            TradeList.Trade trade = newOffer.inferTrade(oldOffer);
            tradeList.set(i, trade);
        }
        return tradeList;
    }

    public final static class Offer {
        final public int slotIndex;
        final public int itemId;
        final String itemName;
        public final int vol;
        final public int price;
        final int transferredVol;
        final int transferredValue;
        final boolean readyToCollect;
        final public OfferStatus status;

        public Offer() {
            this.slotIndex = -1;
            this.itemId = -1;
            this.itemName = null;
            this.vol = 0;
            this.price = 0;
            this.transferredVol = 0;
            this.transferredValue = 0;
            this.status = null;
            this.readyToCollect = false; // fully ready to collect
        }

        public Offer(int index) {
            this.slotIndex = index;
            this.itemId = -1;
            this.itemName = null;
            this.vol = 0;
            this.price = 0;
            this.transferredVol = 0;
            this.transferredValue = 0;
            this.status = null;
            this.readyToCollect = false;
        }

        public Offer(int index, int itemId, String itemName, int vol, int price, int transferredVol,
                     int transferredValue, OfferStatus status, boolean readyToCollect) {
            this.slotIndex = index;
            this.itemId = itemId;
            this.itemName = itemName;
            this.vol = vol;
            this.price = price;
            this.transferredVol = transferredVol;
            this.transferredValue = transferredValue;
            this.status = status;
            this.readyToCollect = readyToCollect;
        }

        public TradeList.Trade inferTrade(Offer oldSlot) {
            int vol = this.transferredVol - oldSlot.transferredVol;
            if (vol <= 0) return null;

            int price = (this.transferredValue - oldSlot.transferredValue) / vol;

            if (this.status == OfferStatus.SELL) {
                vol = -1 * vol; // negative quantity indicates a sell
            }

            TradeList.Trade trade = new TradeList.Trade(Instant.now().getEpochSecond(), this.itemId, this.itemName, vol, price);
            return trade;
        }

        public int getSlotIndex() {
            return this.slotIndex;
        }

        public boolean isReadyToCollect() {
            return this.readyToCollect;
        }
    }

    public enum OfferStatus {
        EMPTY,
        BUY,
        SELL
    }
}
