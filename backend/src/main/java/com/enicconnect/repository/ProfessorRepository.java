package com.enicconnect.repository;

import com.enicconnect.model.Professor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface ProfessorRepository extends JpaRepository<Professor, Long> {
    
    @Query("SELECT p FROM Professor p JOIN p.user u WHERE u.id = :userId")
    Optional<Professor> findByUserId(@Param("userId") Long userId);
    
    List<Professor> findByDepartment(String department);
}
