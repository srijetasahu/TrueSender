package com.truesender.backend.controller;

import com.truesender.backend.model.EmailScan;
import com.truesender.backend.service.EmailScanService;
import com.truesender.backend.service.MlClientService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.Optional;

/**
 * Web controller serving all Thymeleaf pages. Member 2's piece (routing /
 * orchestration), rendering Member 3's HTML templates.
 *
 * Routes (per handover Section 5):
 *   GET  /          - home page, scan form
 *   POST /scan      - receives form, validates, calls service, renders result
 *   GET  /history   - scan history table
 *   GET  /stats     - statistics dashboard
 *   GET  /scan/{id} - single scan detail page
 */
@Controller
public class EmailController {

    private static final int MIN_EMAIL_LENGTH = 10;
    private static final int MAX_EMAIL_LENGTH = 5000;

    private final EmailScanService emailScanService;

    public EmailController(EmailScanService emailScanService) {
        this.emailScanService = emailScanService;
    }

    @GetMapping("/")
    public String homePage(Model model) {
        model.addAttribute("mlServiceOnline", emailScanService.isMlServiceOnline());
        return "index";
    }

    @PostMapping("/scan")
    public String scanEmail(
            @RequestParam String emailText,
            @RequestParam(required = false, defaultValue = "") String senderDisplayName,
            @RequestParam(required = false, defaultValue = "") String senderEmail,
            Model model) {

        // --- Input validation: no DB call, no Python call if this fails ---
        String trimmed = emailText == null ? "" : emailText.trim();

        if (trimmed.length() < MIN_EMAIL_LENGTH) {
            model.addAttribute("error", "Email too short to analyze");
            model.addAttribute("mlServiceOnline", emailScanService.isMlServiceOnline());
            return "index";
        }
        if (emailText.length() > MAX_EMAIL_LENGTH) {
            model.addAttribute("error", "Email too long, max " + MAX_EMAIL_LENGTH + " chars");
            model.addAttribute("mlServiceOnline", emailScanService.isMlServiceOnline());
            return "index";
        }

        try {
            EmailScan result = emailScanService.scanAndSave(emailText, senderDisplayName, senderEmail);
            model.addAttribute("result", result);
        } catch (MlClientService.MlServiceUnavailableException e) {
            model.addAttribute("error", e.getMessage());
        }

        model.addAttribute("mlServiceOnline", emailScanService.isMlServiceOnline());
        return "index";
    }

    @GetMapping("/history")
    public String historyPage(Model model) {
        model.addAttribute("scans", emailScanService.getHistory());
        return "history";
    }

    @GetMapping("/stats")
    public String statsPage(Model model) {
        model.addAttribute("stats", emailScanService.getStats());
        return "stats";
    }

    @GetMapping("/scan/{id}")
    public String scanDetailPage(@PathVariable Long id, Model model) {
        Optional<EmailScan> scan = emailScanService.getById(id);
        if (scan.isEmpty()) {
            model.addAttribute("error", "Scan not found");
            return "history";
        }
        model.addAttribute("scan", scan.get());
        return "detail";
    }
}
