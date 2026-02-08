package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Body;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Header;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.URL;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class RequestResponse extends RequestBase{
    URL url;

    public RequestResponse(){

    }

    public RequestResponse(URL url, String method, List<Header> header, Body body, String description) {
        super(method, header, body, description);
        this.url = url;
    }

    public URL getUrl() {
        return url;
    }

    public void setUrl(URL url) {
        this.url = url;
    }
}
