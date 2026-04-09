package com.enicconnect.repository;

import com.enicconnect.model.Grade;
import com.enicconnect.model.Grade.GradeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

@Repository
public interface GradeRepository extends JpaRepository<Grade, Long> {
    
    List<Grade> findByStudentId(Long studentId);
    
    List<Grade> findByStudentIdAndSubjectId(Long studentId, Long subjectId);
    
    List<Grade> findByProfessorId(Long professorId);
    
    Optional<Grade> findByStudentIdAndSubjectIdAndGradeTypeAndAcademicYear(
        Long studentId, Long subjectId, GradeType gradeType, String academicYear);
    
    @Query("SELECT AVG(g.gradeValue) FROM Grade g WHERE g.student.id = :studentId")
    BigDecimal getAverageGradeByStudent(@Param("studentId") Long studentId);
    
    @Query("SELECT AVG(g.gradeValue) FROM Grade g WHERE g.subject.id = :subjectId")
    BigDecimal getAverageGradeBySubject(@Param("subjectId") Long subjectId);
    
    @Query("SELECT AVG(g.gradeValue) FROM Grade g WHERE g.professor.id = :professorId")
    BigDecimal getAverageGradeByProfessor(@Param("professorId") Long professorId);
    
    @Query("SELECT g FROM Grade g WHERE g.student.id = :studentId ORDER BY g.gradedAt DESC")
    List<Grade> findRecentGradesByStudent(@Param("studentId") Long studentId);
}