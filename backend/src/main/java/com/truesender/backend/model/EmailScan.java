package com.truesender.backend.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * Database entity representing one scanned email and its combined
 * ML + phishing-heuristic verdict. Member 2's piece.
 *
 * Field list matches handover document Section 5 exactly.
 */
@Entity
@Table(name = "email_scans")
public class EmailScan {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(length = 5000, nullable = false)
    private String emailText;

    private String senderDisplayName;
    private String senderEmail;

    // ML classifier result (Member 1's piece)
    private String mlLabel;          // "spam", "ham", or "uncertain"
    private Double mlConfidence;     // max probability, 0.0 - 1.0
    private String confidenceBand;   // HIGH CONFIDENCE / LOW CONFIDENCE / REVIEW MANUALLY
    private Double spamProbability;
    private Double hamProbability;

    // Phishing heuristic result (Member 3's piece)
    private Boolean phishingSuspected;
    private Double phishingRiskScore;
    private Integer phishingTriggeredChecks;
    private Integer phishingTotalChecks;

    @Column(length = 4000)
    private String phishingDetailsJson; // raw per-check breakdown, stored as JSON text

    // Combined verdict
    private String finalVerdict;     // SAFE / SPAM / SUSPICIOUS / HIGH RISK

    private LocalDateTime scannedAt;

    public EmailScan() {
        this.scannedAt = LocalDateTime.now();
    }

    // --- Getters and setters ---

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getEmailText() { return emailText; }
    public void setEmailText(String emailText) { this.emailText = emailText; }

    public String getSenderDisplayName() { return senderDisplayName; }
    public void setSenderDisplayName(String senderDisplayName) { this.senderDisplayName = senderDisplayName; }

    public String getSenderEmail() { return senderEmail; }
    public void setSenderEmail(String senderEmail) { this.senderEmail = senderEmail; }

    public String getMlLabel() { return mlLabel; }
    public void setMlLabel(String mlLabel) { this.mlLabel = mlLabel; }

    public Double getMlConfidence() { return mlConfidence; }
    public void setMlConfidence(Double mlConfidence) { this.mlConfidence = mlConfidence; }

    public String getConfidenceBand() { return confidenceBand; }
    public void setConfidenceBand(String confidenceBand) { this.confidenceBand = confidenceBand; }

    public Double getSpamProbability() { return spamProbability; }
    public void setSpamProbability(Double spamProbability) { this.spamProbability = spamProbability; }

    public Double getHamProbability() { return hamProbability; }
    public void setHamProbability(Double hamProbability) { this.hamProbability = hamProbability; }

    public Boolean getPhishingSuspected() { return phishingSuspected; }
    public void setPhishingSuspected(Boolean phishingSuspected) { this.phishingSuspected = phishingSuspected; }

    public Double getPhishingRiskScore() { return phishingRiskScore; }
    public void setPhishingRiskScore(Double phishingRiskScore) { this.phishingRiskScore = phishingRiskScore; }

    public Integer getPhishingTriggeredChecks() { return phishingTriggeredChecks; }
    public void setPhishingTriggeredChecks(Integer phishingTriggeredChecks) { this.phishingTriggeredChecks = phishingTriggeredChecks; }

    public Integer getPhishingTotalChecks() { return phishingTotalChecks; }
    public void setPhishingTotalChecks(Integer phishingTotalChecks) { this.phishingTotalChecks = phishingTotalChecks; }

    public String getPhishingDetailsJson() { return phishingDetailsJson; }
    public void setPhishingDetailsJson(String phishingDetailsJson) { this.phishingDetailsJson = phishingDetailsJson; }

    public String getFinalVerdict() { return finalVerdict; }
    public void setFinalVerdict(String finalVerdict) { this.finalVerdict = finalVerdict; }

    public LocalDateTime getScannedAt() { return scannedAt; }
    public void setScannedAt(LocalDateTime scannedAt) { this.scannedAt = scannedAt; }
}
