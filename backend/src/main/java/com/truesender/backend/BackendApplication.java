package com.truesender.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the TrueSender Spring Boot backend (Member 2's piece).
 *
 * Run with:
 *   mvn spring-boot:run
 *
 * Then visit:
 *   http://localhost:8080
 *
 * IMPORTANT: the Python ML service (Member 1's piece) must already be
 * running on http://127.0.0.1:8000 before you submit an email here,
 * otherwise classification requests will fail with a friendly error.
 */
@SpringBootApplication
public class BackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(BackendApplication.class, args);
    }
}
