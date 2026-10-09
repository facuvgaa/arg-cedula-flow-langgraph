package com.example.infrastructure.config;

import com.example.application.commands.HireInsurancePolicyService;
import com.example.application.commands.HireInsurancePolicyUseCase;
import com.example.application.queries.CalculateQuoteQueryService;
import com.example.application.queries.CalculateQuoteQueryUseCase;
import com.example.domain.ports.PolicyRepositoryPort;
import com.example.domain.ports.VehicleMarketValuePort;
import com.example.infrastructure.adapters.in.mcp.InsuranceMcpToolAdapter;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ApplicationConfig {

    @Bean
    public CalculateQuoteQueryUseCase calculateQuoteQueryUseCase(VehicleMarketValuePort marketValuePort) {
        return new CalculateQuoteQueryService(marketValuePort);
    }

    @Bean
    public HireInsurancePolicyUseCase hireInsurancePolicyUseCase(
            PolicyRepositoryPort policyRepositoryPort,
            VehicleMarketValuePort marketValuePort
    ) {
        return new HireInsurancePolicyService(policyRepositoryPort, marketValuePort);
    }

    @Bean
    public ToolCallbackProvider insuranceTools(InsuranceMcpToolAdapter insuranceMcpToolAdapter) {
        return MethodToolCallbackProvider.builder()
                .toolObjects(insuranceMcpToolAdapter)
                .build();
    }
}
