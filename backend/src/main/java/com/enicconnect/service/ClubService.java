package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ClubService {
    
    private final ClubRepository clubRepository;
    private final UserRepository userRepository;
    
    @Transactional
    public Club createClub(String name, String description, Long chairUserId) {
        User chairUser = null;
        if (chairUserId != null) {
            chairUser = userRepository.findById(chairUserId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        }
        
        Club club = Club.builder()
            .name(name)
            .description(description)
            .chairUser(chairUser)
            .build();
        
        return clubRepository.save(club);
    }
    
    public Club getClubById(Long id) {
        return clubRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Club not found with id: " + id));
    }
    
    public Club getClubByName(String name) {
        return clubRepository.findByName(name)
            .orElseThrow(() -> new RuntimeException("Club not found with name: " + name));
    }
    
    public List<Club> getAllClubs() {
        return clubRepository.findAll();
    }
    
    public List<Club> getClubsByChair(Long chairUserId) {
        return clubRepository.findByChairUserId(chairUserId);
    }
}