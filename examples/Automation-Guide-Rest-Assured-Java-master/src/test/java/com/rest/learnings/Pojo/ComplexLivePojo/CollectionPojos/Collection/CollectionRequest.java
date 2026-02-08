package com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Collection;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Folder.FolderRequest;
import com.rest.learnings.Pojo.ComplexLivePojo.CollectionPojos.Info;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class CollectionRequest extends CollectionBase {
    List<FolderRequest> item;

    public CollectionRequest(Info info,List<FolderRequest> item) {
        super(info);
        this.item = item;
    }

    public CollectionRequest() {}

    public List<FolderRequest> getItem() {
        return item;
    }

    public void setItem(List<FolderRequest> item) {
        this.item = item;
    }
}
