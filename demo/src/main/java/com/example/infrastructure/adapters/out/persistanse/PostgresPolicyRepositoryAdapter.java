package com.example.infrastructure.adapters.out.persistanse;

import com.example.domain.models.InsurancePolicy;
import com.example.domain.ports.PolicyRepositoryPort;
import com.example.infrastructure.adapters.out.persistanse.entity.PolicyEntity;
import com.example.infrastructure.adapters.out.persistanse.repository.SpringDataPolicyRepository;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
public class PostgresPolicyRepositoryAdapter implements PolicyRepositoryPort {

    private final SpringDataPolicyRepository repository;

    public PostgresPolicyRepositoryAdapter(SpringDataPolicyRepository repository) {
        this.repository = repository;
    }

    @Override
    public InsurancePolicy save(InsurancePolicy policy) {
        PolicyEntity entity = PolicyEntity.builder()
                .policyNumber(policy.policyNumber())
                .customerName(policy.customerName())
                .customerDni(policy.customerDni())
                .customerEmail(policy.customerEmail())
                .licensePlate(policy.licensePlate())
                .vehicleDescription(policy.vehicleDescription())
                .postalCode(policy.postalCode())
                .coverageType(policy.coverageType())
                .monthlyPremium(policy.monthlyPremium())
                .status(policy.status())
                .greenCardPhotoUrl(policy.greenCardPhotoUrl())
                .inspectionPhotosUrl(policy.inspectionPhotosUrl())
                .issuedAt(policy.issuedAt())
                .build();

        PolicyEntity saved = repository.save(entity);
        return toDomain(saved);
    }

    @Override
    public Optional<InsurancePolicy> findByPolicyNumber(String policyNumber) {
        return repository.findByPolicyNumber(policyNumber).map(this::toDomain);
    }

    private InsurancePolicy toDomain(PolicyEntity entity) {
        return new InsurancePolicy(
                entity.getPolicyNumber(),
                entity.getCustomerName(),
                entity.getCustomerDni(),
                entity.getCustomerEmail(),
                entity.getLicensePlate(),
                entity.getVehicleDescription(),
                entity.getPostalCode(),
                entity.getCoverageType(),
                entity.getMonthlyPremium(),
                entity.getStatus(),
                entity.getGreenCardPhotoUrl(),
                entity.getInspectionPhotosUrl(),
                entity.getIssuedAt()
        );
    }
}

