package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Collection;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Info;

@JsonIgnoreProperties(ignoreUnknown = true)
public abstract class CollectionBase {
    Info info;

    public CollectionBase(Info info) {
        this.info = info;
    }

    public CollectionBase() {}

    public Info getInfo() {
        return info;
    }

    public void setInfo(Info info) {
        this.info = info;
    }
}
