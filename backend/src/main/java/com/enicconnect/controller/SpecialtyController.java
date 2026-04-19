package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.model.Specialty;
import com.enicconnect.repository.SpecialtyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/specialties")
@RequiredArgsConstructor
public class SpecialtyController {

    private final SpecialtyRepository specialtyRepository;

    @GetMapping
    public ResponseEntity<ApiResponse<List<Specialty>>> getAllSpecialties() {
        try {
            List<Specialty> specialties = specialtyRepository.findAll();
            return ResponseEntity.ok(ApiResponse.success(specialties));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}
