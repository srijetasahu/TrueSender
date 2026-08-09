package com.truesender.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request body sent FROM Java TO the Python FastAPI service's /analyze endpoint.
 * Field names must match Python's AnalyzeRequest (Pydantic model) exactly,
 * since Jackson serializes this to JSON using these field names.
 *
 * Python expects snake_case ("sender_display_name") while Java convention
 * is camelCase ("senderDisplayName") - @JsonProperty bridges the two
 * naming conventions without either side changing its style.
 */
public class AnalyzeRequestDto {

    private String text;
    private String senderDisplayName;
    private String senderEmail;

    public AnalyzeRequestDto() {}

    public AnalyzeRequestDto(String text, String senderDisplayName, String senderEmail) {
        this.text = text;
        this.senderDisplayName = senderDisplayName;
        this.senderEmail = senderEmail;
    }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    @JsonProperty("sender_display_name")
    public String getSenderDisplayName() { return senderDisplayName; }
    public void setSenderDisplayName(String senderDisplayName) { this.senderDisplayName = senderDisplayName; }

    @JsonProperty("sender_email")
    public String getSenderEmail() { return senderEmail; }
    public void setSenderEmail(String senderEmail) { this.senderEmail = senderEmail; }
}
