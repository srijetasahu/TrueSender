package com.truesender.backend.service;

import com.truesender.backend.dto.AnalyzeRequestDto;
import com.truesender.backend.dto.AnalyzeResponseDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

/**
 * ============================================================
 * THE JAVA <-> PYTHON INTEGRATION CODE.
 * ============================================================
 *
 * Member 2's piece. Calls Member 1's FastAPI service (running separately
 * on http://127.0.0.1:8000) over plain HTTP/REST, exactly like calling
 * any third-party API.
 *
 * How it works:
 *   1. Java builds a small JSON request body (AnalyzeRequestDto)
 *   2. RestTemplate sends a POST request to the Python service's /analyze endpoint
 *   3. Python responds with JSON
 *   4. Jackson (Spring's built-in JSON library) automatically converts
 *      that JSON into a Java object (AnalyzeResponseDto)
 *
 * Includes retry logic: 3 attempts, 1 second wait between attempts, so a
 * momentary hiccup in the Python service doesn't fail the whole scan.
 *
 * If the Python service is still not reachable after retries, this throws
 * a clear exception that the controller catches and shows the user a
 * friendly error - see EmailController.java.
 */
@Service
public class MlClientService {

    private static final int MAX_ATTEMPTS = 3;
    private static final long RETRY_WAIT_MS = 1000;

    private final RestTemplate restTemplate;
    private final String mlServiceBaseUrl;

    public MlClientService(@Value("${ml.service.base-url}") String mlServiceBaseUrl) {
        this.mlServiceBaseUrl = mlServiceBaseUrl;
        this.restTemplate = new RestTemplate();
    }

    /**
     * Calls the Python /analyze endpoint with the email text + sender info.
     * Retries up to MAX_ATTEMPTS times with a 1 second wait between attempts
     * before giving up and throwing MlServiceUnavailableException.
     */
    public AnalyzeResponseDto analyzeEmail(String text, String senderDisplayName, String senderEmail) {
        String url = mlServiceBaseUrl + "/analyze";
        AnalyzeRequestDto requestBody = new AnalyzeRequestDto(text, senderDisplayName, senderEmail);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<AnalyzeRequestDto> requestEntity = new HttpEntity<>(requestBody, headers);

        RuntimeException lastError = null;

        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            try {
                AnalyzeResponseDto response = restTemplate.postForObject(
                        url, requestEntity, AnalyzeResponseDto.class
                );
                if (response == null) {
                    throw new MlServiceUnavailableException("Python ML service returned an empty response.");
                }
                return response;

            } catch (ResourceAccessException e) {
                // Fires when Python service isn't running at all (connection refused)
                lastError = new MlServiceUnavailableException(
                        "Could not reach the Python ML service at " + mlServiceBaseUrl +
                        ". Make sure it's running: cd ml-service && uvicorn main:app --port 8000", e
                );
            } catch (RestClientException e) {
                // Fires on HTTP error responses (4xx/5xx) from Python
                lastError = new MlServiceUnavailableException(
                        "Python ML service returned an error: " + e.getMessage(), e
                );
            }

            if (attempt < MAX_ATTEMPTS) {
                try {
                    Thread.sleep(RETRY_WAIT_MS);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }

        throw lastError;
    }

    /**
     * Simple health check - used to show a "ML service: online/offline" banner.
     */
    public boolean isMlServiceHealthy() {
        try {
            restTemplate.getForObject(mlServiceBaseUrl + "/health", String.class);
            return true;
        } catch (RestClientException e) {
            return false;
        }
    }

    /** Custom exception so the controller can show a clean error page instead of a 500 stack trace. */
    public static class MlServiceUnavailableException extends RuntimeException {
        public MlServiceUnavailableException(String message) { super(message); }
        public MlServiceUnavailableException(String message, Throwable cause) { super(message, cause); }
    }
}
