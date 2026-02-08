package com.rest.learnings.FormAuthentication;

import io.restassured.RestAssured;
import io.restassured.authentication.FormAuthConfig;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.session.SessionFilter;
import io.restassured.http.Cookie;
import io.restassured.http.Cookies;
import io.restassured.response.Response;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.Map;

import static io.restassured.RestAssured.given;

//For execute this test is necessary launch Romanian Coder Example for can execute test about it
public class CookiesExamples {

    @BeforeClass
    public void beforeClass(){
        RestAssured.requestSpecification = new RequestSpecBuilder().
                setBaseUri("https://localhost:8081").
                build();
    }

    @Test
    public void form_authentication_using_csrf_token_cookie_example(){
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
                cookie("JSESSIONID", filter.getSessionId()).
                log().all().
        when().
                get("/profile/index").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void form_authentication_using_csrf_token_cookie_builder_example(){
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

        Cookie cookie = new Cookie.Builder("JSESSIONID", filter.getSessionId()).
                setSecured(true).setHttpOnly(true).setComment("my cookle").build();

        given().
                cookie(cookie).
                log().all().
        when().
                get("/profile/index").
       then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void form_authentication_using_csrf_token_multiple_cookies_example(){
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

        Cookie cookie1 = new Cookie.Builder("JSESSIONID", filter.getSessionId()).
                setSecured(true).setHttpOnly(true).setComment("my cookle1").build();

        Cookie cookie2 = new Cookie.Builder("dummy","dummyValue").build();

        Cookies cookies = new Cookies(cookie1, cookie2);

        given().
                cookies(cookies).
                log().all().
        when().
                get("/profile/index").
        then().
                log().all().
                assertThat().
                statusCode(200);
    }

    @Test
    public void fetch_single_cookie(){
     Response response = given().
                log().all().
        when().
                get("/profile/index").
        then().
                log().all().
                assertThat().
                statusCode(200).
                extract().
                response();

        System.out.println(response.getCookie("JSESSIONID"));
        System.out.println(response.getDetailedCookie("JSESSIONID"));
    }

    @Test
    public void fetch_multiple_cookies(){
        Response response = given().
                log().all().
        when().
                get("/profile/index").
        then().
                log().all().
                assertThat().
                statusCode(200).
                extract().
                response();

        Map<String,String> cookies = response.getCookies();

        //fetch cookies with name and value
        for (Map.Entry<String,String> entry: cookies.entrySet()){
            System.out.println("cookie name" + entry.getKey());
            System.out.println("cookie value" + entry.getValue());
        }

        //fetch cookies with mora details
        Cookies cookies1 = response.getDetailedCookies();
        List<Cookie> cookieList = cookies1.asList();
        for (Cookie cookie: cookieList){
            System.out.println("cookie = " +cookie.toString());
        }
    }
}
