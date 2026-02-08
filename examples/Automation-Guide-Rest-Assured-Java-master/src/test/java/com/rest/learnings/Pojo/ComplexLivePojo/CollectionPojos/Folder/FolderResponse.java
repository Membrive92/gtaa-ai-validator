package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Folder;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.RequestRoot.RequestRootResponse;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class FolderResponse extends FolderBase {
    List<RequestRootResponse> item;

    public FolderResponse(String name, List<RequestRootResponse> item) {
        super(name);
        this.item = item;
    }

    public FolderResponse() {
    }

    public List<RequestRootResponse> getItem() {
        return item;
    }

    public void setItem(List<RequestRootResponse> item) {
        this.item = item;
    }
}
