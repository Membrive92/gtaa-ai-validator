package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.RequestRoot;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public abstract class RequestRootBase {
    private String name;

    public RequestRootBase(String name) {
        this.name = name;
    }

    public RequestRootBase() {
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
