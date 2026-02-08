package com.rest.learnings.Pojo;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rest.learnings.Pojo.simple.SimplePojo;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.ResponseSpecification;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static io.restassured.RestAssured.*;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;

public class PojoExample {
    ResponseSpecification responseSpecification;
    @BeforeClass
    public void beforeClass() {
        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder().
                setBaseUri("https://b9f7a298-1b18-4062-b3ce-6c08731ac0bd.mock.pstmn.io").
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
    public void simple_pojo_example_get_values(){
        SimplePojo simplePojo = new SimplePojo("value1", "value2");

        given().
                body(simplePojo).
        when().
                post("/postSimpleJson").
        then().spec(responseSpecification).
                body("key1", equalTo(simplePojo.getKey1()),
                        "key2", equalTo(simplePojo.getKey2()));
    }

    @Test
    public void simple_pojo_example_set_values(){
        SimplePojo simplePojo = new SimplePojo();
        simplePojo.setKey1("value1");
        simplePojo.setKey2("value2");

        given().
                body(simplePojo).
        when().
                post("/postSimpleJson").
        then().spec(responseSpecification).
                body("key1", equalTo(simplePojo.getKey1()),
                        "key2", equalTo(simplePojo.getKey2()));
    }
    @Test
    public void simple_pojo_example_Deserialization() throws JsonProcessingException {
        SimplePojo simplePojo = new SimplePojo("value1", "value2");

       SimplePojo deserializedPojo = given().
                body(simplePojo).
        when().
                post("/postSimpleJson").
        then().spec(responseSpecification).
                extract().
                response().
                as(SimplePojo.class);

        ObjectMapper objectMapper = new ObjectMapper();
        String deserializedPojoStr = objectMapper.writeValueAsString(deserializedPojo);
        String simplePojoStr = objectMapper.writeValueAsString(simplePojo);
        assertThat(objectMapper.readTree(deserializedPojoStr), equalTo(objectMapper.readTree(simplePojoStr)));
    }
}
