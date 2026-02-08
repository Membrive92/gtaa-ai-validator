package com.rest.framework.spotify.oauth2.api.applicationApi;

import com.rest.framework.spotify.oauth2.api.RestBase;
import com.rest.framework.spotify.oauth2.pojo.Playlist;
import com.rest.framework.spotify.oauth2.utils.ConfigLoader;
import io.restassured.response.Response;

import java.io.FileNotFoundException;

import static com.rest.framework.spotify.oauth2.api.Route.PLAYLISTS;
import static com.rest.framework.spotify.oauth2.api.Route.USERS;
import static com.rest.framework.spotify.oauth2.api.TokenManager.getToken;

public class PlaylistApi {

    public static Response post(Playlist requestPlaylist) throws FileNotFoundException {
        return RestBase.post(USERS + "/" + ConfigLoader.getInstance().getUser() + PLAYLISTS, getToken(), requestPlaylist);
    }

    public static Response post(String token,Playlist requestPlaylist) throws FileNotFoundException {
        return RestBase.post(USERS + "/"  + ConfigLoader.getInstance().getUser() + PLAYLISTS, token, requestPlaylist);
    }

    public static Response get(String playlistId){
        return RestBase.get(PLAYLISTS + "/" + playlistId, getToken());
    }

    public static Response put(String playlistId, Playlist requestPlaylist){
        return RestBase.put(PLAYLISTS + "/" + playlistId, getToken(), requestPlaylist);
    }
}
