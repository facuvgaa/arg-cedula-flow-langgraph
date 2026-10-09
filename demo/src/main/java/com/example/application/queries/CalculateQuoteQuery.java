package com.example.application.queries;

public record CalculateQuoteQuery(
    String brand,
    String model,
    int year,
    String postalCode
) {}

