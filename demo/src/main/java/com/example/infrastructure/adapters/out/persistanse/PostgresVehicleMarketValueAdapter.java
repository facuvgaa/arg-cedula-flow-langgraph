package com.example.infrastructure.adapters.out.persistanse;

import com.example.domain.ports.VehicleMarketValuePort;
import com.example.infrastructure.adapters.out.persistanse.entity.VehicleMarketValueEntity;
import com.example.infrastructure.adapters.out.persistanse.repository.SpringDataVehicleRepository;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.Optional;

@Component
public class PostgresVehicleMarketValueAdapter implements VehicleMarketValuePort {

    private final SpringDataVehicleRepository repository;

    public PostgresVehicleMarketValueAdapter(SpringDataVehicleRepository repository) {
        this.repository = repository;
    }

    @Override
    public Optional<BigDecimal> findEstimatedValue(String brand, String model, int year) {
        String cleanBrand = (brand != null) ? brand.trim() : "";
        String cleanModel = (model != null) ? model.trim().split(" ")[0] : "";

        return repository.findBySpecs(cleanBrand, cleanModel, year)
                .map(VehicleMarketValueEntity::getMarketValue);
    }
}