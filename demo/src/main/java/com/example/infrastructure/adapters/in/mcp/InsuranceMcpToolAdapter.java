package com.example.infrastructure.adapters.in.mcp;

import com.example.application.commands.HireInsurancePolicyCommand;
import com.example.application.commands.HireInsurancePolicyUseCase;
import com.example.application.queries.CalculateQuoteQuery;
import com.example.application.queries.CalculateQuoteQueryUseCase;
import com.example.domain.models.InsurancePolicy;
import com.example.domain.models.InsuranceQuote;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class InsuranceMcpToolAdapter {

    private final CalculateQuoteQueryUseCase calculateQuoteQueryUseCase;
    private final HireInsurancePolicyUseCase hireInsurancePolicyUseCase;

    public InsuranceMcpToolAdapter(
            CalculateQuoteQueryUseCase calculateQuoteQueryUseCase,
            HireInsurancePolicyUseCase hireInsurancePolicyUseCase
    ) {
        this.calculateQuoteQueryUseCase = calculateQuoteQueryUseCase;
        this.hireInsurancePolicyUseCase = hireInsurancePolicyUseCase;
    }

    @Tool(
        name = "calculate_insurance_quote",
        description = "Calcula cotizaciones estimadas de pólizas de seguros para un vehículo automotor."
    )
    public InsuranceQuote calculateInsuranceQuote(
            @ToolParam(description = "Marca del vehículo (ej: Ford, Renault)") String brand,
            @ToolParam(description = "Modelo o versión del vehículo (ej: EcoSport, Kangoo)") String model,
            @ToolParam(description = "Año de fabricación (ej: 2010)") int year,
            @ToolParam(description = "Código postal de guarda (ej: 4000)") String postalCode
    ) {
        CalculateQuoteQuery query = new CalculateQuoteQuery(brand, model, year, postalCode);
        return calculateQuoteQueryUseCase.handle(query);
    }

    @Tool(
        name = "hire_insurance_policy",
        description = "Contrata y emite una póliza de seguro automotor oficial para un cliente."
    )
    public InsurancePolicy hireInsurancePolicy(
            @ToolParam(description = "Nombre completo del titular del vehículo") String customerName,
            @ToolParam(description = "DNI o documento de identidad del titular") String customerDni,
            @ToolParam(description = "Correo electrónico del titular") String customerEmail,
            @ToolParam(description = "Patente o dominio del vehículo (ej: AB123CD)") String licensePlate,
            @ToolParam(description = "Marca del vehículo (ej: Ford, Renault)") String brand,
            @ToolParam(description = "Modelo del vehículo (ej: EcoSport, Kangoo)") String model,
            @ToolParam(description = "Año de fabricación (ej: 2010)") int year,
            @ToolParam(description = "Código postal (ej: 4000)") String postalCode,
            @ToolParam(description = "Tipo de cobertura seleccionada: RESPONSABILIDAD_CIVIL, TERCEROS_COMPLETO o TODO_RIESGO") String coverageType,
            @ToolParam(description = "URL o key en MinIO de la foto de la tarjeta verde (opcional)") String greenCardPhotoUrl,
            @ToolParam(description = "URLs o keys en MinIO de las fotos del vehículo para inspección (opcional)") String inspectionPhotosUrl
    ) {
        HireInsurancePolicyCommand command = new HireInsurancePolicyCommand(
                customerName,
                customerDni,
                customerEmail,
                licensePlate,
                brand,
                model,
                year,
                postalCode,
                coverageType,
                greenCardPhotoUrl,
                inspectionPhotosUrl
        );
        return hireInsurancePolicyUseCase.handle(command);
    }
}