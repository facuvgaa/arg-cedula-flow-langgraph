package com.example.application.commands;

import com.example.domain.models.InsurancePolicy;
import com.example.domain.ports.PolicyRepositoryPort;
import com.example.domain.ports.VehicleMarketValuePort;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.UUID;

public class HireInsurancePolicyService implements HireInsurancePolicyUseCase {

    private final PolicyRepositoryPort policyRepositoryPort;
    private final VehicleMarketValuePort marketValuePort;

    public HireInsurancePolicyService(PolicyRepositoryPort policyRepositoryPort, VehicleMarketValuePort marketValuePort) {
        this.policyRepositoryPort = policyRepositoryPort;
        this.marketValuePort = marketValuePort;
    }

    @Override
    public InsurancePolicy handle(HireInsurancePolicyCommand command) {
        // 1. Obtener valor estimado del vehículo
        BigDecimal valorAuto = marketValuePort.findEstimatedValue(command.brand(), command.model(), command.year())
                .orElse(BigDecimal.valueOf(8_500_000.00));

        // 2. Factor de zona por código postal
        BigDecimal zonaFactor = (command.postalCode() != null && command.postalCode().startsWith("4000"))
                ? BigDecimal.valueOf(0.90)
                : BigDecimal.valueOf(1.00);

        // 3. Calcular prima según cobertura elegida
        BigDecimal unscaledPremium = switch (command.coverageType().toUpperCase()) {
            case "TODO_RIESGO" -> valorAuto.multiply(BigDecimal.valueOf(0.0078)).multiply(zonaFactor);
            case "TERCEROS_COMPLETO" -> valorAuto.multiply(BigDecimal.valueOf(0.0042)).multiply(zonaFactor);
            case "RESPONSABILIDAD_CIVIL" -> BigDecimal.valueOf(25_000.00).multiply(zonaFactor);
            default -> throw new IllegalArgumentException("Tipo de cobertura no válida: " + command.coverageType());
        };
        BigDecimal monthlyPremium = unscaledPremium.setScale(2, RoundingMode.HALF_UP);

        // 4. Generar número de póliza único
        String policyNumber = "POL-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        String vehicleDescription = String.format("%s %s (%d)",
                command.brand().trim().toUpperCase(),
                command.model().trim().toUpperCase(),
                command.year());

        // 5. Instanciar póliza de dominio
        InsurancePolicy policy = new InsurancePolicy(
                policyNumber,
                command.customerName(),
                command.customerDni(),
                command.customerEmail(),
                command.licensePlate() != null ? command.licensePlate().trim().toUpperCase() : "NO_ASIGNADA",
                vehicleDescription,
                command.postalCode(),
                command.coverageType().toUpperCase(),
                monthlyPremium,
                "ACTIVE",
                command.greenCardPhotoUrl(),
                command.inspectionPhotosUrl(),
                LocalDateTime.now()
        );

        // 6. Persistir en base de datos
        return policyRepositoryPort.save(policy);
    }
}

