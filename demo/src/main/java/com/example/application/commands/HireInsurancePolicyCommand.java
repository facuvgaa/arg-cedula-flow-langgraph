package com.example.application.commands;

public record HireInsurancePolicyCommand(
    String customerName,
    String customerDni,
    String customerEmail,
    String licensePlate,
    String brand,
    String model,
    int year,
    String postalCode,
    String coverageType,        
    String greenCardPhotoUrl,
    String inspectionPhotosUrl 
) {}

