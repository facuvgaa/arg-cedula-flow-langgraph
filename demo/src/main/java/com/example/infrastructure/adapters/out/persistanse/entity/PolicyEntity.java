package com.example.infrastructure.adapters.out.persistanse.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "policies")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PolicyEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "policy_number", nullable = false, unique = true)
    private String policyNumber;

    @Column(name = "customer_name", nullable = false)
    private String customerName;

    @Column(name = "customer_dni")
    private String customerDni;

    @Column(name = "customer_email")
    private String customerEmail;

    @Column(name = "license_plate")
    private String licensePlate;

    @Column(name = "vehicle_description", nullable = false)
    private String vehicleDescription;

    @Column(name = "postal_code")
    private String postalCode;

    @Column(name = "coverage_type", nullable = false)
    private String coverageType;

    @Column(name = "monthly_premium", nullable = false)
    private BigDecimal monthlyPremium;

    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "green_card_photo_url")
    private String greenCardPhotoUrl;

    @Column(name = "inspection_photos_url", columnDefinition = "TEXT")
    private String inspectionPhotosUrl;

    @Column(name = "issued_at", nullable = false)
    private LocalDateTime issuedAt;
}

