package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Body;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Header;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class RequestRequest extends RequestBase{
    private String url;

    public RequestRequest(){

    }

    public RequestRequest(String url, String method, List<Header> header, Body body, String description) {
        super(method, header, body, description);
        this.url = url;
    }


    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }
}
