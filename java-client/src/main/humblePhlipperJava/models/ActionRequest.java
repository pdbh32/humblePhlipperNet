package humblePhlipperJava.models;

public class ActionRequest {
    public Portfolio portfolio;
    public String user;
    public int membersDaysLeft;
    public boolean tradeRestricted;

    public ActionRequest(Portfolio portfolio, String user, int membersDaysLeft, boolean tradeRestricted) {
        this.portfolio = portfolio;
        this.user = user;
        this.membersDaysLeft = membersDaysLeft;
        this.tradeRestricted = tradeRestricted;
    }
}