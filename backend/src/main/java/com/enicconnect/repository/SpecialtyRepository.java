package com.enicconnect.repository;

import com.enicconnect.model.Specialty;
import com.enicconnect.model.Specialty.SpecialtyCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface SpecialtyRepository extends JpaRepository<Specialty, Long> {
    
    Optional<Specialty> findByCode(SpecialtyCode code);
    
    Optional<Specialty> findByName(String name);
}