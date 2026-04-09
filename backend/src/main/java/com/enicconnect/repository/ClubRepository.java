package com.enicconnect.repository;

import com.enicconnect.model.Club;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface ClubRepository extends JpaRepository<Club, Long> {
    
    Optional<Club> findByName(String name);
    
    List<Club> findByChairUserId(Long chairUserId);
}