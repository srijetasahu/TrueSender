package com.truesender.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.truesender.backend.dto.AnalyzeResponseDto;
import com.truesender.backend.model.EmailScan;
import com.truesender.backend.repository.EmailScanRepository;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Business logic layer: orchestrates calling the Python ML service,
 * saving the combined result to the database, and computing statistics
 * for the /stats dashboard. Member 2's piece.
 */
@Service
public class EmailScanService {

    private final MlClientService mlClientService;
    private final EmailScanRepository emailScanRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public EmailScanService(MlClientService mlClientService, EmailScanRepository emailScanRepository) {
        this.mlClientService = mlClientService;
        this.emailScanRepository = emailScanRepository;
    }

    /**
     * Full pipeline: send email text to Python -> get combined verdict -> save to DB.
     */
    public EmailScan scanAndSave(String emailText, String senderDisplayName, String senderEmail) {
        AnalyzeResponseDto result = mlClientService.analyzeEmail(emailText, senderDisplayName, senderEmail);

        EmailScan scan = new EmailScan();
        scan.setEmailText(emailText);
        scan.setSenderDisplayName(senderDisplayName);
        scan.setSenderEmail(senderEmail);

        scan.setMlLabel(result.getMlResult().getLabel());
        scan.setMlConfidence(result.getMlResult().getConfidence());
        scan.setConfidenceBand(result.getMlResult().getConfidenceBand());
        scan.setSpamProbability(result.getMlResult().getSpamProbability());
        scan.setHamProbability(result.getMlResult().getHamProbability());

        scan.setPhishingSuspected(result.isPhishingSuspected());
        scan.setPhishingRiskScore(result.getPhishingRiskScore());
        scan.setPhishingTriggeredChecks(result.getPhishingTriggeredChecks());
        scan.setPhishingTotalChecks(result.getPhishingTotalChecks());

        scan.setFinalVerdict(result.getFinalVerdict());

        try {
            scan.setPhishingDetailsJson(objectMapper.writeValueAsString(result.getPhishingDetails()));
        } catch (Exception e) {
            scan.setPhishingDetailsJson("{}");
        }

        return emailScanRepository.save(scan);
    }

    public List<EmailScan> getHistory() {
        return emailScanRepository.findAllByOrderByScannedAtDesc();
    }

    public Optional<EmailScan> getById(Long id) {
        return emailScanRepository.findById(id);
    }

    public boolean isMlServiceOnline() {
        return mlClientService.isMlServiceHealthy();
    }

    /**
     * Aggregate counts for the /stats dashboard.
     */
    public Map<String, Object> getStats() {
        long total = emailScanRepository.count();
        long spamCount = emailScanRepository.countByMlLabel("spam");
        long hamCount = emailScanRepository.countByMlLabel("ham");
        long phishingCount = emailScanRepository.countByPhishingSuspectedTrue();
        long safeCount = emailScanRepository.countByFinalVerdictStartingWith("SAFE");
        long highRiskCount = emailScanRepository.countByFinalVerdictStartingWith("HIGH RISK");

        Map<String, Object> stats = new HashMap<>();
        stats.put("total", total);
        stats.put("spamCount", spamCount);
        stats.put("hamCount", hamCount);
        stats.put("phishingCount", phishingCount);
        stats.put("safeCount", safeCount);
        stats.put("highRiskCount", highRiskCount);

        stats.put("spamPercent", total == 0 ? 0.0 : (spamCount * 100.0) / total);
        stats.put("phishingPercent", total == 0 ? 0.0 : (phishingCount * 100.0) / total);
        stats.put("safePercent", total == 0 ? 0.0 : (safeCount * 100.0) / total);

        List<EmailScan> recent = emailScanRepository.findAllByOrderByScannedAtDesc();
        stats.put("recentScans", recent.size() > 5 ? recent.subList(0, 5) : recent);

        return stats;
    }
}
