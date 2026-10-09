package com.example.infrastructure.adapters.out.persistanse.repository;

import com.example.infrastructure.adapters.out.persistanse.entity.PolicyEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SpringDataPolicyRepository extends JpaRepository<PolicyEntity, Long> {
    Optional<PolicyEntity> findByPolicyNumber(String policyNumber);
}

