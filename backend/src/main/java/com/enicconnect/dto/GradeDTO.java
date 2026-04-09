package com.enicconnect.dto;

import com.enicconnect.model.Grade;
import lombok.Data;
import javax.validation.constraints.DecimalMax;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

@Data
public class GradeDTO {
    
    @NotNull(message = "Student ID is required")
    private Long studentId;
    
    @NotNull(message = "Subject ID is required")
    private Long subjectId;
    
    @NotNull(message = "Grade type is required")
    private Grade.GradeType gradeType;
    
    @NotNull(message = "Grade value is required")
    @DecimalMin(value = "0.0", message = "Grade must be at least 0")
    @DecimalMax(value = "20.0", message = "Grade must not exceed 20")
    private BigDecimal gradeValue;
    
    private String comment;
    
    @NotNull(message = "Academic year is required")
    private String academicYear;
}