package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ProfessorService {

    private final ProfessorRepository professorRepository;
    private final UserRepository userRepository;
    private final GradeRepository gradeRepository;

    @Transactional
    public Professor createProfessor(Long userId, String department, String officeEmail) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("User not found with id: " + userId));

        Professor professor = Professor.builder()
            .user(user)
            .department(department != null ? department : "Non défini")
            .officeEmail(officeEmail != null ? officeEmail : user.getEmail())
            .build();

        return professorRepository.save(professor);
    }

    public Professor getProfessorById(Long id) {
        return professorRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Professor not found with id: " + id));
    }

    public Professor getProfessorByUserId(Long userId) {
        return professorRepository.findByUserId(userId)
            .orElseThrow(() -> new RuntimeException("Professor not found for user id: " + userId));
    }

    public Double getProfessorAverageGrade(Long professorId) {
        try {
            java.math.BigDecimal avg = gradeRepository.getAverageGradeByProfessor(professorId);
            return avg != null ? avg.doubleValue() : null;
        } catch (Exception e) {
            return null;
        }
    }
}
