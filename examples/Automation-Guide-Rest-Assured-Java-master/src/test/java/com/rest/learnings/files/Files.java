package com.rest.learnings.files;

import io.restassured.filter.log.LogDetail;
import io.restassured.filter.log.RequestLoggingFilter;
import io.restassured.filter.log.ResponseLoggingFilter;
import org.testng.annotations.Test;

import java.io.*;

import static io.restassured.RestAssured.given;

public class Files {

    @Test
    public void upload_file_multipart_form_data(){
        String attributes = "{\"name\":\"temp.txt\",\"parent\":{\"id\":\"123456\"}}";
        given().
                baseUri("https://postman-echo.com").
                multiPart("file", new File("src/main/resources/temp.txt")).
                multiPart("attributes", attributes, "multipart/form-data").
                log().all().
         when().
                post("/post").
         then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    //using Appium for download a file example
    public void download_file() throws IOException {
       InputStream is = given().
                baseUri("https://raw.githubusercontent.com").
                log().all().
        when().
                get("/appium/appium/master/sample-code/apps/ApiDemos-debug.apk").
        then().
                log().all().
                extract().
                response().asInputStream();
        OutputStream os = new FileOutputStream(new File("src/main/resources/ApiDemos-debug.apk"));
        byte[] bytes = new byte[is.available()];
        is.read(bytes);
        os.write(bytes);
        os.close();
    }

    @Test
    public void loggingFile() throws FileNotFoundException {
        PrintStream FileOutPutStream = new PrintStream(new File("src/main/resources/restAssured.log"));
        given().
                baseUri("https://postman-echo.com").
                filter(new RequestLoggingFilter(LogDetail.BODY, FileOutPutStream)).
                filter(new ResponseLoggingFilter(LogDetail.STATUS, FileOutPutStream)).
        when().
                get("/get").
        then().
                assertThat().
                statusCode(200);
    }
}
