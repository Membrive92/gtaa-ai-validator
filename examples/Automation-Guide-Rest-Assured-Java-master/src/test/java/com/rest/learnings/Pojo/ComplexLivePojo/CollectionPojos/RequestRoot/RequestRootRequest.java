package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.RequestRoot;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Request.RequestRequest;

@JsonIgnoreProperties(ignoreUnknown = true)
public class RequestRootRequest extends RequestRootBase {
    RequestRequest request;

    public RequestRootRequest(String name, RequestRequest request) {
        super(name);
        this.request = request;
    }

    public RequestRootRequest() {
    }

    public RequestRequest getRequest() {
        return request;
    }

    public void setRequest(RequestRequest request) {
        this.request = request;
    }
}
