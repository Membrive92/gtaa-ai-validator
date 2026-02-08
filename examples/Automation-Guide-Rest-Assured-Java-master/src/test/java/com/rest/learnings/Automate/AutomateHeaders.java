package com.rest.learnings.Automate;

import io.restassured.http.Header;
import io.restassured.http.Headers;
import org.testng.annotations.Test;

import java.util.HashMap;
import java.util.List;

import static io.restassured.RestAssured.given;

public class AutomateHeaders {
    @Test
    public void multiple_headers() {
        Header header = new Header("header", "value1");
        Header matchHeader = new Header("x-mock-match-request-headers", "header");

        given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                header(header).
                header(matchHeader).
        when().
                get("/get").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void multiple_headers_using_headers() {
        Header header = new Header("header", "value1");
        Header matchHeader = new Header("x-mock-match-request-headers", "header");

        Headers headers = new Headers(header, matchHeader);

        given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                headers(headers).
                header(matchHeader).
        when().
                get("/get").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void multiple_headers_using_map() {
        HashMap<String, String> headersMap = new HashMap<String, String>();
        headersMap.put("header", "value1");
        headersMap.put("x-mock-match-request-headers", "header");

        given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                headers(headersMap).
        when().
                get("/get").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void multiple_value_headers_in_headers() {
        Header header1 = new Header("multiValueHeader", "value1");
        Header header2 = new Header("multiValueHeader", "header");
        Headers headers = new Headers(header1, header2);

        given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
               // header("multipleValueHeader", "value1","value2").
               headers(headers).
        when().
                get("/get").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void assert_response_headers() {
        Header header1 = new Header("multiValueHeader", "value1");
        Header header2 = new Header("x-mock-match-request-headers", "header");
        Headers headers = new Headers(header1, header2);

        given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                        headers(headers).
        when().
                get("/get").
        then().
                assertThat().
                statusCode(200).
                //header("responseHeader", "resValue1");
                 headers("responseHeader", "resValue2",
                        "X-RateLimit-Limit", "120");
    }

    @Test
    public void extract_response_headers() {
        Header header1 = new Header("multiValueHeader", "value1");
        Header header2 = new Header("x-mock-match-request-headers", "header");
        Headers headers = new Headers(header1, header2);

       Headers extractHeaders =  given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                headers(headers).
        when().
                get("/get").
        then().
                assertThat().
                statusCode(200).
                extract().
                headers();
       for (Header header : extractHeaders) {
           System.out.println("header name = " + header.getName() +  ", ");
           System.out.println("header value = " + header.getValue());
       }

     /*   System.out.println("header name = " +extractHeaders.get("responseHeader").getName());
        System.out.println("header value = " +extractHeaders.get("responseHeader").getValue());
        System.out.println("header value = " +extractHeaders.getValue("responseHeader"));*/
    }

    @Test
    public void extract_multivalue_response_headers() {
        HashMap<String, String> headersMap = new HashMap<String, String>();
        headersMap.put("header", "value1");
        headersMap.put("x-mock-match-request-headers", "header");

        Headers extractHeaders = given().
                baseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
                headers(headersMap).
        when().
                get("/get").
        then().
                assertThat().
                statusCode(200).
                extract().
                headers();

        List<String> values = extractHeaders.getValues("multiValueHeader");
        for (String headerValue:values) {
            System.out.println(headerValue);
        }
    }
}
