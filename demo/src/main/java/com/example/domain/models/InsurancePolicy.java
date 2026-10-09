package com.example.domain.models;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record InsurancePolicy(
    String policyNumber,
    String customerName,
    String customerDni,
    String customerEmail,
    String licensePlate,
    String vehicleDescription,
    String postalCode,
    String coverageType,
    BigDecimal monthlyPremium,
    String status,
    String greenCardPhotoUrl,
    String inspectionPhotosUrl,
    LocalDateTime issuedAt
) {}
