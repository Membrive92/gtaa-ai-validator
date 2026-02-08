package com.rest.learnings.Imports;

import org.testng.annotations.Test;

import static com.rest.learnings.Utils.Utils.postmanApiKey;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.is;

public class StaticImports {

    @Test
    public void simple_test_case() {
        given().
                baseUri("https://api.postman.com").
                header("x-api-key", postmanApiKey()).
        when().
                get("/workspaces").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }
}
