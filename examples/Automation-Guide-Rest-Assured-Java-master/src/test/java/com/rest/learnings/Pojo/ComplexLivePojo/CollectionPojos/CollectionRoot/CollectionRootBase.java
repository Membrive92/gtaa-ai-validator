package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.CollectionRoot;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public abstract class CollectionRootBase {

    public CollectionRootBase() {
    }
}
