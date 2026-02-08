package com.rest.framework.spotify.oauth2.api;

import com.rest.framework.spotify.oauth2.utils.ConfigLoader;
import io.restassured.http.ContentType;
import io.restassured.response.Response;

import java.io.FileNotFoundException;
import java.time.Instant;
import java.util.HashMap;

import static com.rest.framework.spotify.oauth2.api.SpecBuilder.getResponseSpec;
import static io.restassured.RestAssured.given;

public class TokenManager {
    private static String access_token;
    private static Instant expiry_time;

    public static String getToken(){
        try{
            if(access_token == null || Instant.now().isAfter(expiry_time)){
                Response response = renewToken();
                access_token = response.path("access_token");
                int expiryDurationInSeconds = response.path("expires_in");
                expiry_time = Instant.now().plusSeconds(expiryDurationInSeconds - 300);
            } else {
                System.out.println("Token is used");
            }

        } catch (Exception e){
            throw  new RuntimeException("Failed to get token");

        }
        return access_token;
    }

    private static Response renewToken() throws FileNotFoundException {
        HashMap<String,String> formParams = new HashMap<String,String>();
        formParams.put("client_id", ConfigLoader.getInstance().getClientId());
        formParams.put("client_secret",ConfigLoader.getInstance().getClientSecret());
        formParams.put("refresh_token",ConfigLoader.getInstance().getRefreshToken());
        formParams.put("grant_type",ConfigLoader.getInstance().getGrantType());

        Response response = RestBase.postAccount(formParams);

        if (response.statusCode() != 200){
            throw new RuntimeException("Renew token has failed");
        }
        return response;
    }
}
