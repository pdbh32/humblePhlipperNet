package humblePhlipperNet.controllers;

import humblePhlipperNet.models.*;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class Network {
    private static final String BASE_URL = "http://localhost:5000";
    private static final Gson gson = new Gson();

    public static Event getNextCommand(NextCommandRequest payload) {
        String endpoint = "/getNextCommand";
        String response = postJsonToServer(endpoint, payload);
        if (response == null) {
            return new Event(System.currentTimeMillis() / 1000, Event.Label.ERROR, null, null, null, null, null, "null response from server");
        }
        try {
            return gson.fromJson(response, Event.class);
        } catch (JsonSyntaxException e) {
            e.printStackTrace();
            return new Event(System.currentTimeMillis() / 1000, Event.Label.ERROR, null, null, null, null, null, e.getMessage());
        }
    }

    public static void reportEvents(ReportEventsRequest payload) {
        String endpoint = "/reportEvents";
        postJsonToServer(endpoint, payload);  // ignore response
    }

    private static String postJsonToServer(String endpoint, Object payload) {
        try {
            String jsonPayload = gson.toJson(payload);
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
}
