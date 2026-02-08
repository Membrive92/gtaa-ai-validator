package com.rest.learnings.oauth2;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import io.restassured.specification.ResponseSpecification;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.Base64;
import java.util.HashMap;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.matchesPattern;

//for this tests is mandatory create a goolge account and config an app in developers.google
public class GmailApi {
    RequestSpecification requestSpecification;
    ResponseSpecification responseSpecification;
    String access_token = "REPLACE_WITH_YOUR_OAUTH_TOKEN";
    @BeforeClass
    public void beforeClass() {
        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder();
        requestSpecBuilder.setBaseUri("https://gmail.googleapis.com").
                addHeader("Authorization", "Bearer "+access_token).
                setContentType(ContentType.JSON).
                log(LogDetail.ALL);
        requestSpecification = requestSpecBuilder.build();

        ResponseSpecBuilder responseSpecBuilder = new ResponseSpecBuilder().
                expectStatusCode(200).
                expectContentType(ContentType.JSON).
                log(LogDetail.ALL);
        responseSpecification = responseSpecBuilder.build();
    }

    @Test
    public void getUserProfile() {
        given(requestSpecification).
                basePath("/gmail/v1").
                pathParam("userid", "joseapitst@gmail.com").
        when().
                get("/users/{userid}/profile").
        then().spec(responseSpecification);
    }

    @Test
    public void sendMessage() {
        String msg = "From: joseapitst@gmail.com\n" +
                "To: joseapitst@gmail.com\n" +
                "Subject: Test Email\n" +
                "\n" +
                "Sending from Gmail Api";

        String base64UrlEncodeMsg = Base64.getUrlEncoder().encodeToString(msg.getBytes());
        HashMap<String,String> payload = new HashMap<String,String>();
        payload.put("raw", base64UrlEncodeMsg);

        given(requestSpecification).
                basePath("/gmail/v1").
                pathParam("userid", "joseapitst@gmail.com").
                body(payload).
        when().
                post("/users/{userid}/messages/send").
        then().spec(responseSpecification);
    }
}
