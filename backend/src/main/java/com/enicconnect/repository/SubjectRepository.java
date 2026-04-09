package com.enicconnect.repository;

import com.enicconnect.model.Subject;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface SubjectRepository extends JpaRepository<Subject, Long> {
    
    Optional<Subject> findByCode(String code);
    
    Optional<Subject> findByName(String name);
    
    List<Subject> findBySpecialtyId(Long specialtyId);
    
    List<Subject> findBySemester(Byte semester);
    
    List<Subject> findByIsCoreTrue();
    
    @Query("SELECT s FROM Subject s WHERE s.specialty.id = :specialtyId AND s.semester = :semester")
    List<Subject> findBySpecialtyAndSemester(@Param("specialtyId") Long specialtyId, @Param("semester") Byte semester);
}