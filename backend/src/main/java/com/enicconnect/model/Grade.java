package com.enicconnect.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "grades")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Grade {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne
    @JoinColumn(name = "student_id", nullable = false)
    private Student student;
    
    @ManyToOne
    @JoinColumn(name = "subject_id", nullable = false)
    private Subject subject;
    
    @ManyToOne
    @JoinColumn(name = "professor_id")
    private Professor professor;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "grade_type", nullable = false)
    private GradeType gradeType;
    
    @Column(name = "grade_value", nullable = false, precision = 5, scale = 2)
    private BigDecimal gradeValue;
    
    @Column(columnDefinition = "TEXT")
    private String comment;
    
    @Column(name = "graded_at", nullable = false)
    private LocalDateTime gradedAt;
    
    @Column(name = "academic_year", nullable = false, length = 9)
    private String academicYear;
    
    @PrePersist
    protected void onCreate() {
        gradedAt = LocalDateTime.now();
    }
    
    public enum GradeType {
        CC1, CC2, CC3, EXAM
    }
}