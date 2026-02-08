package com.rest.learnings.Utils;

import java.util.Base64;

public class Utils {
    public static String postmanApiKey(){
        String encoderString = "UE1BSy02NGNlMjJiNDc1Nzk2MTc0Y2Q5M2RmYmEtZDVmOWI0ZDFmNmFmYmY2M2JhOGYzMjQxM2U3OWU3MTc2YQ==";
        byte[] bytesDecodes = Base64.getDecoder().decode(encoderString);

        return new String(bytesDecodes);
    }

    public static void base64Example(){
        String text64 = "username:password";

        String base64Encoded = Base64.getEncoder().encodeToString(text64.getBytes());
        System.out.println("Encoded = " + base64Encoded);
        byte[] decodedBytes = Base64.getDecoder().decode(base64Encoded);
        System.out.println("Decoded = " + new String(decodedBytes));
    }
}
