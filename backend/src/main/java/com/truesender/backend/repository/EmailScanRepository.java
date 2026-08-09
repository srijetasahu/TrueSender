package com.truesender.backend.repository;

import com.truesender.backend.model.EmailScan;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Spring Data JPA repository - gives us save(), findAll(), findById(),
 * count(), deleteById() for free, no SQL needed. Member 2's piece.
 *
 * Custom methods below are auto-implemented by Spring Data purely from
 * their method names (it parses "findAllByOrderByScannedAtDesc" etc. and
 * generates the matching SQL at startup).
 */
@Repository
public interface EmailScanRepository extends JpaRepository<EmailScan, Long> {

    List<EmailScan> findAllByOrderByScannedAtDesc();

    Optional<EmailScan> findById(Long id);

    long countByMlLabel(String mlLabel);

    long countByPhishingSuspectedTrue();

    long countByFinalVerdictStartingWith(String prefix);
}
