package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@Service
@RequiredArgsConstructor
public class StudentService {
    
    private final StudentRepository studentRepository;
    private final GradeRepository gradeRepository;
    private final UserRepository userRepository;
    private final SpecialtyRepository specialtyRepository;
    
    @Transactional
    public Student createStudent(Long userId, Long specialtyId, String academicLevel, 
                                  String groupName, Short enrollmentYear, Byte currentSemester) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found"));
        
        Specialty specialty = specialtyRepository.findById(specialtyId)
            .orElseThrow(() -> new RuntimeException("Specialty not found"));
        
        Student student = Student.builder()
            .user(user)
            .specialty(specialty)
            .academicLevel(academicLevel)
            .groupName(groupName)
            .enrollmentYear(enrollmentYear)
            .currentSemester(currentSemester)
            .riskScore(BigDecimal.ZERO)
            .riskLevel(Student.RiskLevel.STABLE)
            .build();
        
        return studentRepository.save(student);
    }
    
    @Transactional
    public void updateRiskScore(Long studentId) {
        Student student = getStudentById(studentId);
        
        BigDecimal avgGrade = gradeRepository.getAverageGradeByStudent(studentId);
        if (avgGrade == null) {
            avgGrade = BigDecimal.ZERO;
        }
        
        // Calculate risk score: lower grades = higher risk
        // Formula: (100 - (averageGrade * 5))
        BigDecimal riskScore = BigDecimal.valueOf(100)
            .subtract(avgGrade.multiply(BigDecimal.valueOf(5)));
        
        riskScore = riskScore.max(BigDecimal.ZERO).min(BigDecimal.valueOf(100));
        riskScore = riskScore.setScale(2, RoundingMode.HALF_UP);
        
        student.setRiskScore(riskScore);
        
        // Determine risk level
        if (riskScore.compareTo(BigDecimal.valueOf(70)) >= 0) {
            student.setRiskLevel(Student.RiskLevel.HIGH_RISK);
        } else if (riskScore.compareTo(BigDecimal.valueOf(40)) >= 0) {
            student.setRiskLevel(Student.RiskLevel.ATTENTION_REQUIRED);
        } else {
            student.setRiskLevel(Student.RiskLevel.STABLE);
        }
        
        studentRepository.save(student);
    }
    
    public Student getStudentById(Long id) {
        return studentRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Student not found with id: " + id));
    }
    
    public Student getStudentByUserId(Long userId) {
        return studentRepository.findByUserId(userId)
            .orElseThrow(() -> new RuntimeException("Student not found for user id: " + userId));
    }
    
    public List<Student> getStudentsAtRisk() {
        return studentRepository.findByRiskLevel(Student.RiskLevel.HIGH_RISK);
    }
    
    public List<Student> getStudentsBySpecialty(Long specialtyId) {
        return studentRepository.findBySpecialtyId(specialtyId);
    }
    
    public List<Student> getAllStudents() {
        return studentRepository.findAll();
    }
    
    public Long countStudentsByRiskLevel(Student.RiskLevel riskLevel) {
        return studentRepository.countByRiskLevel(riskLevel);
    }
    
    public BigDecimal getStudentAverageGrade(Long studentId) {
        BigDecimal avg = gradeRepository.getAverageGradeByStudent(studentId);
        return avg != null ? avg : BigDecimal.ZERO;
    }
}