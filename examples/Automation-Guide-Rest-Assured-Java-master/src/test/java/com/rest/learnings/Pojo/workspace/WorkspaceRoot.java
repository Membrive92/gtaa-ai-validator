package com.rest.learnings.Pojo.workspace;

public class WorkspaceRoot {
    Workspace workspace;
    private String type;
    private String description;

    public WorkspaceRoot(){}

    public WorkspaceRoot(Workspace workspace){
        this.workspace = workspace;
    }

    public Workspace getWorkspace() {
        return workspace;
    }

    public void setWorkspace(Workspace workspace) {
        this.workspace = workspace;
    }
}
