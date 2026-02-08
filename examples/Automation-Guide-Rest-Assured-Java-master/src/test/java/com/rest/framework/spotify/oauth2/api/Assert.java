package com.rest.framework.spotify.oauth2.api;

import com.rest.framework.spotify.oauth2.pojo.Error;
import com.rest.framework.spotify.oauth2.pojo.Playlist;
import io.qameta.allure.Step;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;

public class Assert {
    @Step
    public static void assertPlaylistEqual(Playlist responsePlaylist, Playlist requestPlaylist){
        assertThat(responsePlaylist.getName(), equalTo(requestPlaylist.getName()));
        assertThat(responsePlaylist.getDescription(), equalTo(requestPlaylist.getDescription()));
        assertThat(responsePlaylist.get_public(), equalTo(requestPlaylist.get_public()));
    }

    @Step
    public static void assertStatusCode(int actualStatusCode, StatusCodes statusCodes){
        assertThat(actualStatusCode, equalTo(statusCodes.code));
    }

    @Step
    public static void assertError(Error responseError, StatusCodes statusCodes){
        assertThat(responseError.getError().getStatus(), equalTo(statusCodes.code));
        assertThat(responseError.getError().getMessage(), equalTo(statusCodes.msg));
    }
}
