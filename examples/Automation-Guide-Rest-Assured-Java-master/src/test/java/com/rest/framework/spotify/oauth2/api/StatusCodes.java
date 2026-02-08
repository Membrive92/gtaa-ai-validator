package com.rest.framework.spotify.oauth2.api;

public enum StatusCodes {
    CODE_200(200,""),
    CODE_201(201,""),
    CODE_400(400,"Missing required field: name"),
    CODE_401(401,"Invalid access token");

    public final int code;
    public final String msg;

    StatusCodes(int code,String msg){
        this.code = code;
        this.msg = msg;
    }

}
