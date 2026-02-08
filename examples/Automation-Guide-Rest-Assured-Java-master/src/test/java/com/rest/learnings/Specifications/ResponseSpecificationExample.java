package com.rest.learnings.Specifications;

import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static com.rest.learnings.Utils.Utils.postmanApiKey;
import static io.restassured.RestAssured.get;
import static io.restassured.RestAssured.requestSpecification;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;


public class ResponseSpecificationExample {
    @BeforeClass
    public void beforeClass() {
        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder();
        requestSpecBuilder.setBaseUri("https://api.postman.com");
        requestSpecBuilder.addHeader("X-Api-Key", postmanApiKey());
        requestSpecBuilder.log(LogDetail.ALL);
        requestSpecification = requestSpecBuilder.build();

     /*   responseSpecification = RestAssured.expect().
                statusCode(200).
                contentType(ContentType.JSON);*/

        ResponseSpecBuilder responseSpecBuilder = new ResponseSpecBuilder().
                expectStatusCode(200).
                expectContentType(ContentType.JSON).
                log(LogDetail.ALL);
       RestAssured.responseSpecification = responseSpecBuilder.build();
    }

    @Test
    public void validate_status_code() {
        get("/workspaces");
    }

    @Test
    public void validate_response_body() {
        Response response =   get("/workspaces").
                then().
                extract().
                response();
        assertThat(response.path("workspaces[0].name"), equalTo("Team Workspace"));
    }
}

