package com.enicconnect.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "students")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Student {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @OneToOne
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;
    
    @ManyToOne
    @JoinColumn(name = "specialty_id", nullable = false)
    private Specialty specialty;
    
    @Column(name = "academic_level", nullable = false, length = 50)
    private String academicLevel;
    
    @Column(name = "group_name", length = 50)
    private String groupName;
    
    @Column(name = "enrollment_year")
    private Short enrollmentYear;
    
    @Column(name = "current_semester")
    private Byte currentSemester;
    
    @Column(name = "risk_score", nullable = false, precision = 5, scale = 2)
    private BigDecimal riskScore = BigDecimal.ZERO;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level", nullable = false)
    private RiskLevel riskLevel = RiskLevel.STABLE;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
    
    public enum RiskLevel {
        STABLE, ATTENTION_REQUIRED, HIGH_RISK
    }
}