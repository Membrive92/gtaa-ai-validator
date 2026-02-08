package com.rest.learnings.Serialization;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.ResponseSpecification;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.HashMap;

import static com.rest.learnings.Utils.Utils.postmanApiKey;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.matchesPattern;

public class JacksonAPI_JSONObject {
    ResponseSpecification customResponseSpecification;

    @BeforeClass
    public void beforeClass() {
        RequestSpecBuilder requestSpecBuilder = new RequestSpecBuilder();
        requestSpecBuilder.setBaseUri("https://api.postman.com");
        requestSpecBuilder.addHeader("X-Api-Key", postmanApiKey()).
                setContentType(ContentType.JSON).
                log(LogDetail.ALL);
        requestSpecification = requestSpecBuilder.build();

        ResponseSpecBuilder responseSpecBuilder = new ResponseSpecBuilder().
                expectStatusCode(200).
                expectContentType(ContentType.JSON).
                log(LogDetail.ALL);
        RestAssured.responseSpecification = responseSpecBuilder.build();
    }

    @Test
    public void validate_post_request_payload_json_array_as_map() throws JsonProcessingException {
        HashMap<String, Object> mainObject = new HashMap<String, Object>();

        HashMap<String, String> nestedObject = new HashMap<String, String>();
        nestedObject.put("name","JacksonWorkspace");
        nestedObject.put("type", "personal");
        nestedObject.put("description", "Rest Assured and Jackson");

        mainObject.put("workspace", nestedObject);

        ObjectMapper objectMapper = new ObjectMapper();
        String mainObjectStr = objectMapper.writeValueAsString(mainObject);

        given().
                body(mainObjectStr).
        when().
                post("/workspaces").
        then().spec(responseSpecification).
                assertThat().
                body("workspace.name", equalTo("JacksonWorkspace"),
                        "workspace.id", matchesPattern("^[a-z0-9-]{36}$"));
    }

    @Test
    public void serialize_json_using_jackson() throws JsonProcessingException {
        ObjectMapper objectMapper = new ObjectMapper();
        ObjectNode nestedObjectNode = objectMapper.createObjectNode();
        nestedObjectNode.put("name","JacksonWorkspace");
        nestedObjectNode.put("type", "personal");
        nestedObjectNode.put("description", "Rest Assured and Jackson");

       ObjectNode mainObjectNode = objectMapper.createObjectNode();
       mainObjectNode.set("workspace", nestedObjectNode);

       String mainObjectStr = objectMapper.writeValueAsString(mainObjectNode);

        given().
                body(mainObjectStr).
        when().
                post("/workspaces").
        then().spec(responseSpecification).
                assertThat().
                body("workspace.name", equalTo("JacksonWorkspace"),
                        "workspace.id", matchesPattern("^[a-z0-9-]{36}$"));
    }
}
