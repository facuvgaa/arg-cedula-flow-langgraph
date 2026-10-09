package com.example.infrastructure.adapters.out.persistanse.repository;


import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.example.infrastructure.adapters.out.persistanse.entity.VehicleMarketValueEntity;

import java.util.Optional;

public interface SpringDataVehicleRepository extends JpaRepository<VehicleMarketValueEntity, Long> {

    @Query("SELECT v FROM VehicleMarketValueEntity v " +
           "WHERE UPPER(v.brand) = UPPER(:brand) " +
           "AND UPPER(v.model) LIKE UPPER(CONCAT('%', :model, '%')) " +
           "AND v.yearFabrication = :year")
    Optional<VehicleMarketValueEntity> findBySpecs(
        @Param("brand") String brand,
        @Param("model") String model,
        @Param("year") Integer year
    );
}
