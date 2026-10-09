package com.example.infrastructure.adapters.out.persistanse.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "vehicle_market_values")
public class VehicleMarketValueEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String brand;
    private String model;

    @Column(name = "year_fabrication")
    private Integer yearFabrication;

    @Column(name = "market_value")
    private BigDecimal marketValue;

    public VehicleMarketValueEntity() {}

    public BigDecimal getMarketValue() {
        return marketValue;
    }
}
