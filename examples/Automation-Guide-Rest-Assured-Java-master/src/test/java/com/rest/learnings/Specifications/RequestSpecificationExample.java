package com.rest.learnings.Specifications;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.response.Response;
import io.restassured.specification.QueryableRequestSpecification;
import io.restassured.specification.SpecificationQuerier;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;


import static com.rest.learnings.Utils.Utils.postmanApiKey;
import static io.restassured.RestAssured.*;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.is;


public class RequestSpecificationExample {

    @BeforeClass
    public void beforeClass() {
     /*   requestSpecification = with().
                baseUri("https://api.postman.com").
                header("X-Api-Key", postmanApiKey());*/

        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder();
        requestSpecBuilder.setBaseUri("https://api.postman.com");
        requestSpecBuilder.addHeader("X-Api-Key", postmanApiKey());
        requestSpecBuilder.log(LogDetail.ALL);

        //default requestSpecification is a variable defined in RestAssured
        requestSpecification = requestSpecBuilder.build();

    }
    //To query or retrieve details from RequestSpecification
    @Test
    public void queryTest() {
        QueryableRequestSpecification queryableRequestSpecification = SpecificationQuerier.
                query(requestSpecification);
        System.out.println(queryableRequestSpecification.getBaseUri());
    }

    @Test
    public void validate_status_code() {
        Response response = get("/workspaces").then().log().all().extract().response();
        assertThat(response.statusCode(), is(equalTo(200)));
    }

    @Test
    public void validate_response_body() {
        Response response = get("/workspaces").then().log().all().extract().response();
        assertThat(response.statusCode(), is(equalTo(200)));
        assertThat(response.path("workspaces[0].name"), equalTo("Team Workspace"));
    }

}
