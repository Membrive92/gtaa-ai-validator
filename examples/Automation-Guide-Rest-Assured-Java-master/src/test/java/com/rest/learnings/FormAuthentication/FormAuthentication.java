package com.rest.learnings.FormAuthentication;

import io.restassured.RestAssured;
import io.restassured.authentication.FormAuthConfig;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.session.SessionFilter;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static io.restassured.RestAssured.given;

//For execute this test is necessary launch Romanian Coder Example for can execute test about it
public class FormAuthentication {

    @BeforeClass
    public void beforeClass(){
        RestAssured.requestSpecification = new RequestSpecBuilder().
                setBaseUri("https://localhost:8081").
                build();
    }

    @Test
    public void form_authentication_using_csrf_token(){
        SessionFilter filter = new SessionFilter();
        given().
                auth().form("dan","dan123", new FormAuthConfig("/signin","txtUsername","txtPassword").
                        withAdditionalField("_csrf")).
                filter(filter).
                log().all().
        when().
                get("/login").
        then().
                log().all().
                assertThat().
                statusCode(200);

        System.out.println("Session id - " + filter.getSessionId());

        given().
                sessionId(filter.getSessionId()).
                log().all().
        when().
                get("/profile/index").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }
}
