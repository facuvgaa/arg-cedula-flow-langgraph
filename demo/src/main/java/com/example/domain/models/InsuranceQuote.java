package com.example.domain.models;

import java.math.BigDecimal;
import java.util.Map;

public record InsuranceQuote(
    String vehicleDescription,
    BigDecimal vehicleMarketValue,
    String postalCode,
    Map<String, BigDecimal> coverages
){}