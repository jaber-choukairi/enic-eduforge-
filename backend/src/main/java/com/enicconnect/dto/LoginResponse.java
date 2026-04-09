package com.enicconnect.dto;

import lombok.Builder;
import lombok.Data;
import java.math.BigDecimal;

@Data
@Builder
public class LoginResponse {
    private String token;
    private Long userId;
    private Long studentId;
    private Long professorId;
    private String email;
    private String firstName;
    private String lastName;
    private String role;
    private String specialty;
    private String department;
    private BigDecimal riskScore;
    private String riskLevel;
    private String message;
}