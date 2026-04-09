package com.enicconnect.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "subjects")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Subject {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(length = 30, unique = true)
    private String code;
    
    @Column(nullable = false, unique = true, length = 120)
    private String name;
    
    @Column(nullable = false, precision = 4, scale = 2)
    private BigDecimal coefficient = BigDecimal.ONE;
    
    @ManyToOne
    @JoinColumn(name = "specialty_id")
    private Specialty specialty;
    
    @Column(name = "academic_level", length = 50)
    private String academicLevel;
    
    private Byte semester;
    
    @Column(name = "is_core", nullable = false)
    private Boolean isCore = false;
}