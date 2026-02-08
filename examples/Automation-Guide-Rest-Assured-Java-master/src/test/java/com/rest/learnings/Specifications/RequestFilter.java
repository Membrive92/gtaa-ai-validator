package com.rest.learnings.Specifications;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.filter.log.RequestLoggingFilter;
import io.restassured.filter.log.ResponseLoggingFilter;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.PrintStream;

import static io.restassured.RestAssured.*;


public class RequestFilter {

    @BeforeClass
    public void beforeClass() throws FileNotFoundException {
        PrintStream FileOutPutStream = new PrintStream(new File("src/main/resources/restAssured.log"));

        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder().
                addFilter(new RequestLoggingFilter(LogDetail.BODY, FileOutPutStream)).
                addFilter(new ResponseLoggingFilter(LogDetail.STATUS, FileOutPutStream));
        requestSpecification = requestSpecBuilder.build();

        ResponseSpecBuilder responseSpecBuilder = new ResponseSpecBuilder();
        responseSpecification = responseSpecBuilder.build();
    }

    @Test
    public void loggingFilter() throws FileNotFoundException {
        given(requestSpecification).
                baseUri("https://postman-echo.com").
        when().
                get("/get").
        then().spec(responseSpecification).
                assertThat().
                statusCode(200);
    }
}
