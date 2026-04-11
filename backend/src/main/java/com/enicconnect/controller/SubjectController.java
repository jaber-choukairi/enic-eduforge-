package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.model.Subject;
import com.enicconnect.repository.SubjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/subjects")
@RequiredArgsConstructor
public class SubjectController {

    private final SubjectRepository subjectRepository;

    @GetMapping
    public ResponseEntity<ApiResponse<List<Subject>>> getAllSubjects() {
        try {
            List<Subject> subjects = subjectRepository.findAll();
            return ResponseEntity.ok(ApiResponse.success(subjects));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/specialty/{specialtyId}")
    public ResponseEntity<ApiResponse<List<Subject>>> getSubjectsBySpecialty(@PathVariable Long specialtyId) {
        try {
            List<Subject> subjects = subjectRepository.findBySpecialtyId(specialtyId);
            return ResponseEntity.ok(ApiResponse.success(subjects));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}
