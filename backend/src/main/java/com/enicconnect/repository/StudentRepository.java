package com.enicconnect.repository;

import com.enicconnect.model.Student;
import com.enicconnect.model.Student.RiskLevel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

@Repository
public interface StudentRepository extends JpaRepository<Student, Long> {
    
    Optional<Student> findByUserId(Long userId);
    
    List<Student> findByRiskLevel(RiskLevel riskLevel);
    
    List<Student> findBySpecialtyId(Long specialtyId);
    
    @Query("SELECT s FROM Student s WHERE s.riskScore > :threshold ORDER BY s.riskScore DESC")
    List<Student> findHighRiskStudents(@Param("threshold") BigDecimal threshold);
    
    @Query("SELECT AVG(s.riskScore) FROM Student s WHERE s.specialty.id = :specialtyId")
    Double getAverageRiskScoreBySpecialty(@Param("specialtyId") Long specialtyId);
    
    @Query("SELECT COUNT(s) FROM Student s WHERE s.riskLevel = :riskLevel")
    Long countByRiskLevel(@Param("riskLevel") RiskLevel riskLevel);
}