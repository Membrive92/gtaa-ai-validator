package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Folder;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.RequestRoot.RequestRootRequest;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class FolderRequest extends FolderBase {
    List<RequestRootRequest> item;

    public FolderRequest(String name, List<RequestRootRequest> item) {
       super(name);
        this.item = item;
    }

    public FolderRequest() {
    }

    public List<RequestRootRequest> getItem() {
        return item;
    }

    public void setItem(List<RequestRootRequest> item) {
        this.item = item;
    }
}
