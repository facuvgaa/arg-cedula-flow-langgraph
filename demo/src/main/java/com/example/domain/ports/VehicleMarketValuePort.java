package com.example.domain.ports;

import java.math.BigDecimal;
import java.util.Optional;

public interface VehicleMarketValuePort {
    Optional<BigDecimal> findEstimatedValue(String brand, String model, int year);
}

