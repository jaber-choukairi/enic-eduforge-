package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.util.List;

@Service
@RequiredArgsConstructor
public class GradeService {
    
    private final GradeRepository gradeRepository;
    private final StudentRepository studentRepository;
    private final SubjectRepository subjectRepository;
    private final ProfessorRepository professorRepository;
    private final StudentService studentService;
    
    @Transactional
    public Grade publishGrade(Long studentId, Long subjectId, Long professorId, 
                              Grade.GradeType gradeType, BigDecimal gradeValue, 
                              String comment, String academicYear) {
        
        Student student = studentRepository.findById(studentId)
            .orElseThrow(() -> new RuntimeException("Student not found"));
        
        Subject subject = subjectRepository.findById(subjectId)
            .orElseThrow(() -> new RuntimeException("Subject not found"));
        
        Professor professor = professorRepository.findById(professorId)
            .orElseThrow(() -> new RuntimeException("Professor not found"));
        
        Grade grade = Grade.builder()
            .student(student)
            .subject(subject)
            .professor(professor)
            .gradeType(gradeType)
            .gradeValue(gradeValue)
            .comment(comment)
            .academicYear(academicYear)
            .build();
        
        Grade savedGrade = gradeRepository.save(grade);
        
        // Update student's risk score after publishing grades
        studentService.updateRiskScore(studentId);
        
        return savedGrade;
    }
    
    public List<Grade> getStudentGrades(Long studentId) {
        return gradeRepository.findByStudentId(studentId);
    }
    
    public List<Grade> getStudentGradesBySubject(Long studentId, Long subjectId) {
        return gradeRepository.findByStudentIdAndSubjectId(studentId, subjectId);
    }
    
    public List<Grade> getProfessorGrades(Long professorId) {
        return gradeRepository.findByProfessorId(professorId);
    }
    
    public BigDecimal getStudentAverage(Long studentId) {
        return gradeRepository.getAverageGradeByStudent(studentId);
    }
    
    public BigDecimal getSubjectAverage(Long subjectId) {
        return gradeRepository.getAverageGradeBySubject(subjectId);
    }
    
    public List<Grade> getRecentGrades(Long studentId) {
        return gradeRepository.findRecentGradesByStudent(studentId);
    }
}