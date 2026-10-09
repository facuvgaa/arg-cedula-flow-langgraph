package com.example.application.commands;

import com.example.domain.models.InsurancePolicy;

public interface HireInsurancePolicyUseCase {
    InsurancePolicy handle(HireInsurancePolicyCommand command);
}

