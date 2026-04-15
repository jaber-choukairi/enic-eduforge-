package com.enicconnect.controller;

import com.enicconnect.dto.*;
import com.enicconnect.model.*;
import com.enicconnect.service.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;
    private final StudentService studentService;
    private final ProfessorService professorService;
    private final PasswordEncoder passwordEncoder;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<LoginResponse>> login(@Valid @RequestBody LoginRequest request) {
        try {
            User user = userService.getUserByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Email ou mot de passe incorrect"));

            if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
                throw new RuntimeException("Email ou mot de passe incorrect");
            }

            if (!user.getIsActive()) {
                throw new RuntimeException("Compte désactivé. Contactez l'administrateur.");
            }

            LoginResponse.LoginResponseBuilder responseBuilder = LoginResponse.builder()
                .userId(user.getId())
                .email(user.getEmail())
                .firstName(user.getFirstName())
                .lastName(user.getLastName())
                .role(user.getRole().name())
                .message("Connexion réussie");

            if (user.getRole() == User.UserRole.STUDENT) {
                try {
                    Student student = studentService.getStudentByUserId(user.getId());
                    responseBuilder.studentId(student.getId())
                        .specialty(student.getSpecialty() != null ? student.getSpecialty().getCode().name() : null)
                        .riskScore(student.getRiskScore())
                        .riskLevel(student.getRiskLevel().name());
                } catch (Exception e) { /* student profile optional */ }
            }

            if (user.getRole() == User.UserRole.PROFESSOR || user.getRole() == User.UserRole.CHAIR) {
                try {
                    Professor professor = professorService.getProfessorByUserId(user.getId());
                    responseBuilder.professorId(professor.getId())
                        .department(professor.getDepartment());
                } catch (Exception e) { /* professor profile optional */ }
            }

            return ResponseEntity.ok(ApiResponse.success(responseBuilder.build()));

        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<LoginResponse>> register(@Valid @RequestBody RegisterRequest request) {
        try {
            // Check email uniqueness with friendly message
            if (userService.getUserByEmail(request.getEmail()).isPresent()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error("Cet email est déjà utilisé. Veuillez vous connecter."));
            }

            User user = userService.createUser(
                request.getFirstName(), request.getLastName(),
                request.getEmail(), passwordEncoder.encode(request.getPassword()),
                request.getRole()
            );

            LoginResponse.LoginResponseBuilder responseBuilder = LoginResponse.builder()
                .userId(user.getId())
                .email(user.getEmail())
                .firstName(user.getFirstName())
                .lastName(user.getLastName())
                .role(user.getRole().name())
                .message("Compte créé avec succès");

            if (request.getRole() == User.UserRole.STUDENT) {
                Long specialtyId = request.getSpecialtyId() != null ? request.getSpecialtyId() : 1L;
                String academicLevel = request.getAcademicLevel() != null ? request.getAcademicLevel() : "L1";
                try {
                    Student student = studentService.createStudent(
                        user.getId(),
                        specialtyId,
                        academicLevel,
                        request.getGroupName(),
                        request.getEnrollmentYearAsShort(),
                        request.getCurrentSemesterAsByte()
                    );
                    responseBuilder.studentId(student.getId())
                        .specialty(student.getSpecialty() != null ? student.getSpecialty().getCode().name() : null)
                        .riskScore(student.getRiskScore())
                        .riskLevel(student.getRiskLevel().name());
                } catch (Exception e) {
                    // Log but don't fail — user is created, profile can be set later
                    System.err.println("Warning: could not create student profile: " + e.getMessage());
                }
            }

            if (request.getRole() == User.UserRole.PROFESSOR || request.getRole() == User.UserRole.CHAIR) {
                String department = request.getDepartment() != null ? request.getDepartment() : "Non défini";
                try {
                    Professor professor = professorService.createProfessor(
                        user.getId(), department, request.getOfficeEmail()
                    );
                    responseBuilder.professorId(professor.getId())
                        .department(professor.getDepartment());
                } catch (Exception e) {
                    System.err.println("Warning: could not create professor profile: " + e.getMessage());
                }
            }

            return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Compte créé avec succès", responseBuilder.build()));

        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error(e.getMessage()));
        }
    }
}
