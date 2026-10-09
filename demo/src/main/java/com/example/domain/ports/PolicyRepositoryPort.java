package com.example.domain.ports;

import com.example.domain.models.InsurancePolicy;
import java.util.Optional;

public interface PolicyRepositoryPort {
    InsurancePolicy save(InsurancePolicy policy);
    Optional<InsurancePolicy> findByPolicyNumber(String policyNumber);
}

