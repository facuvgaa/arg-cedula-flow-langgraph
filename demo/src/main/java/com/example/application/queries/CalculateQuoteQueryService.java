package com.example.application.queries;

import com.example.domain.models.InsuranceQuote;
import com.example.domain.ports.VehicleMarketValuePort;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;

public class CalculateQuoteQueryService implements CalculateQuoteQueryUseCase {

    private final VehicleMarketValuePort marketValuePort;

    public CalculateQuoteQueryService(VehicleMarketValuePort marketValuePort) {
        this.marketValuePort = marketValuePort;
    }

    @Override
    public InsuranceQuote handle(CalculateQuoteQuery query) {
        BigDecimal valorAuto = marketValuePort.findEstimatedValue(query.brand(), query.model(), query.year())
                .orElse(BigDecimal.valueOf(8_500_000.00));

        BigDecimal zonaFactor = (query.postalCode() != null && query.postalCode().startsWith("4000"))
                ? BigDecimal.valueOf(0.90)
                : BigDecimal.valueOf(1.00);

        BigDecimal rc = BigDecimal.valueOf(25_000.00).multiply(zonaFactor);
        BigDecimal terceros = valorAuto.multiply(BigDecimal.valueOf(0.0042)).multiply(zonaFactor);
        BigDecimal todoRiesgo = valorAuto.multiply(BigDecimal.valueOf(0.0078)).multiply(zonaFactor);

        Map<String, BigDecimal> coverages = Map.of(
            "RESPONSABILIDAD_CIVIL", rc.setScale(2, RoundingMode.HALF_UP),
            "TERCEROS_COMPLETO", terceros.setScale(2, RoundingMode.HALF_UP),
            "TODO_RIESGO", todoRiesgo.setScale(2, RoundingMode.HALF_UP)
        );

        String description = String.format("%s %s (%d)",
                query.brand().trim().toUpperCase(),
                query.model().trim().toUpperCase(),
                query.year());

        return new InsuranceQuote(description, valorAuto, query.postalCode(), coverages);
    }
}
