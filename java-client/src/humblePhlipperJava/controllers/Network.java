package humblePhlipperJava.controllers;

import humblePhlipperJava.models.ActionData;
import humblePhlipperJava.models.Portfolio;
import humblePhlipperJava.models.TradeList;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class Network {
    private static final String BASE_URL = "http://localhost:5000";
    private static final Gson gson = new Gson();

    public static ActionData requestActionData(Portfolio portfolio, String user, boolean members, boolean tradeRestricted) {
        String endpoint = "/getActionData";
        RequestWrapper body = new RequestWrapper(portfolio, user, members, tradeRestricted);
        String response = postJsonToServer(endpoint, body);
        if (response == null) {
            return new ActionData(ActionData.Action.ERROR, null, null, null, null, "null response from server");
        }
        try {
            return gson.fromJson(response, ActionData.class);
        } catch (JsonSyntaxException e) {
            e.printStackTrace();
            return new ActionData(ActionData.Action.ERROR, null, null, null, null, e.getMessage());
        }
    }

    public static void sendNewTradeList(TradeList tradeList, String user) {
        String endpoint = "/sendTradeList";
        TradeWrapper body = new TradeWrapper(tradeList, user);
        postJsonToServer(endpoint, body);  // ignore response
    }

    private static String postJsonToServer(String endpoint, Object body) {
        try {
            String jsonPayload = gson.toJson(body);
            HttpURLConnection conn = (HttpURLConnection) new URL(BASE_URL + endpoint).openConnection();

            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonPayload.getBytes());
                os.flush();
            }

            int code = conn.getResponseCode();
            if (code != 200 && code != 204) { // 200 = OK, 204 = No Content
                System.err.println("Server returned error: " + conn.getResponseCode());
                return null;
            }

            try (BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()))) {
                return in.readLine();  // Can be null if endpoint returns nothing
            }

        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    static class RequestWrapper {
        Portfolio portfolio;
        String user;
        boolean members;
        boolean tradeRestricted;

        public RequestWrapper(Portfolio portfolio, String user, boolean members, boolean tradeRestricted) {
            this.portfolio = portfolio;
            this.user = user;
            this.members = members;
            this.tradeRestricted = tradeRestricted;
        }
    }

    private static class TradeWrapper {
        TradeList tradeList;
        String user;

        public TradeWrapper(TradeList tradeList, String user) {
            this.tradeList = tradeList;
            this.user = user;
        }
    }
}
