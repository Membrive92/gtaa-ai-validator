package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.CollectionRoot;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Collection.CollectionRequest;

@JsonIgnoreProperties(ignoreUnknown = true)
public class CollectionRootRequest extends CollectionRootBase {


    CollectionRequest collection;

    public CollectionRootRequest(CollectionRequest collection) {
        this.collection = collection;
    }

    public  CollectionRootRequest() {}
    public CollectionRequest getCollection() {
        return collection;
    }

    public void setCollection(CollectionRequest collection) {
        this.collection = collection;
    }
}
