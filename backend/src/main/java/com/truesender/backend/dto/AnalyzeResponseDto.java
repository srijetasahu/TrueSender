package com.truesender.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

/**
 * Response DTO matching the JSON shape returned by Python's /analyze
 * endpoint (FastAPI's AnalyzeResponse Pydantic model). Jackson deserializes
 * the HTTP response body into this class automatically.
 *
 * @JsonIgnoreProperties(ignoreUnknown = true) makes this resilient: if
 * Member 1 adds new fields to the Python response later, Java won't crash.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class AnalyzeResponseDto {

    @JsonProperty("ml_result")
    private MlResult mlResult;

    @JsonProperty("phishing_suspected")
    private boolean phishingSuspected;

    @JsonProperty("phishing_risk_score")
    private double phishingRiskScore;

    @JsonProperty("phishing_triggered_checks")
    private int phishingTriggeredChecks;

    @JsonProperty("phishing_total_checks")
    private int phishingTotalChecks;

    @JsonProperty("phishing_details")
    private Map<String, Object> phishingDetails;

    @JsonProperty("final_verdict")
    private String finalVerdict;

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MlResult {
        private String label;
        private double confidence;

        @JsonProperty("confidence_band")
        private String confidenceBand;

        @JsonProperty("spam_probability")
        private double spamProbability;

        @JsonProperty("ham_probability")
        private double hamProbability;

        public String getLabel() { return label; }
        public void setLabel(String label) { this.label = label; }

        public double getConfidence() { return confidence; }
        public void setConfidence(double confidence) { this.confidence = confidence; }

        public String getConfidenceBand() { return confidenceBand; }
        public void setConfidenceBand(String confidenceBand) { this.confidenceBand = confidenceBand; }

        public double getSpamProbability() { return spamProbability; }
        public void setSpamProbability(double spamProbability) { this.spamProbability = spamProbability; }

        public double getHamProbability() { return hamProbability; }
        public void setHamProbability(double hamProbability) { this.hamProbability = hamProbability; }
    }

    public MlResult getMlResult() { return mlResult; }
    public void setMlResult(MlResult mlResult) { this.mlResult = mlResult; }

    public boolean isPhishingSuspected() { return phishingSuspected; }
    public void setPhishingSuspected(boolean phishingSuspected) { this.phishingSuspected = phishingSuspected; }

    public double getPhishingRiskScore() { return phishingRiskScore; }
    public void setPhishingRiskScore(double phishingRiskScore) { this.phishingRiskScore = phishingRiskScore; }

    public int getPhishingTriggeredChecks() { return phishingTriggeredChecks; }
    public void setPhishingTriggeredChecks(int phishingTriggeredChecks) { this.phishingTriggeredChecks = phishingTriggeredChecks; }

    public int getPhishingTotalChecks() { return phishingTotalChecks; }
    public void setPhishingTotalChecks(int phishingTotalChecks) { this.phishingTotalChecks = phishingTotalChecks; }

    public Map<String, Object> getPhishingDetails() { return phishingDetails; }
    public void setPhishingDetails(Map<String, Object> phishingDetails) { this.phishingDetails = phishingDetails; }

    public String getFinalVerdict() { return finalVerdict; }
    public void setFinalVerdict(String finalVerdict) { this.finalVerdict = finalVerdict; }
}
