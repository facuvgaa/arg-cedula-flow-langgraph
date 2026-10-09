package com.example.application.queries;

import com.example.domain.models.InsuranceQuote;

public interface CalculateQuoteQueryUseCase {
    InsuranceQuote handle(CalculateQuoteQuery query);
}

