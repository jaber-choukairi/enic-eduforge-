package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.dto.GradeDTO;
import com.enicconnect.model.Grade;
import com.enicconnect.model.Professor;
import com.enicconnect.model.Resource;
import com.enicconnect.model.Student;
import com.enicconnect.service.GradeService;
import com.enicconnect.service.ProfessorService;
import com.enicconnect.service.ResourceService;
import com.enicconnect.service.StudentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/professors")
@RequiredArgsConstructor
public class ProfessorController {
    
    private final ProfessorService professorService;
    private final GradeService gradeService;
    private final ResourceService resourceService;
    private final StudentService studentService;
    
    @GetMapping("/{professorId}/dashboard")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getProfessorDashboard(@PathVariable Long professorId) {
        try {
            Professor professor = professorService.getProfessorById(professorId);
            Double averageGrade = professorService.getProfessorAverageGrade(professorId);
            List<Resource> pendingResources = resourceService.getPendingResources();
            List<Student> atRiskStudents = studentService.getStudentsAtRisk();
            
            Map<String, Object> dashboard = new HashMap<>();
            dashboard.put("professorId", professor.getId());
            dashboard.put("name", professor.getUser().getFirstName() + " " + professor.getUser().getLastName());
            dashboard.put("department", professor.getDepartment());
            dashboard.put("averageGradeGiven", averageGrade);
            dashboard.put("pendingResourcesCount", pendingResources.size());
            dashboard.put("atRiskStudentsCount", atRiskStudents.size());
            dashboard.put("pendingResources", pendingResources);
            dashboard.put("atRiskStudents", atRiskStudents);
            
            return ResponseEntity.ok(ApiResponse.success(dashboard));
            
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/{professorId}/grades")
    public ResponseEntity<ApiResponse<Grade>> publishGrade(@PathVariable Long professorId, 
                                                            @Valid @RequestBody GradeDTO gradeDTO) {
        try {
            Grade grade = gradeService.publishGrade(
                gradeDTO.getStudentId(),
                gradeDTO.getSubjectId(),
                professorId,
                gradeDTO.getGradeType(),
                gradeDTO.getGradeValue(),
                gradeDTO.getComment(),
                gradeDTO.getAcademicYear()
            );
            return ResponseEntity.ok(ApiResponse.success("Grade published successfully", grade));
            
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{professorId}/students")
    public ResponseEntity<ApiResponse<List<Student>>> getProfessorStudents(@PathVariable Long professorId) {
        // This would need a mapping table between professors and students
        // For now, return all students
        try {
            List<Student> students = studentService.getAllStudents();
            return ResponseEntity.ok(ApiResponse.success(students));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{professorId}/resources/pending")
    public ResponseEntity<ApiResponse<List<Resource>>> getPendingResources(@PathVariable Long professorId) {
        try {
            List<Resource> pendingResources = resourceService.getPendingResources();
            return ResponseEntity.ok(ApiResponse.success(pendingResources));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/resources/{resourceId}/approve")
    public ResponseEntity<ApiResponse<Resource>> approveResource(@PathVariable Long resourceId, 
                                                                   @RequestParam Long professorId) {
        try {
            Resource resource = resourceService.approveResource(resourceId, professorId);
            return ResponseEntity.ok(ApiResponse.success("Resource approved successfully", resource));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/resources/{resourceId}/reject")
    public ResponseEntity<ApiResponse<Resource>> rejectResource(@PathVariable Long resourceId, 
                                                                 @RequestParam Long professorId) {
        try {
            Resource resource = resourceService.rejectResource(resourceId, professorId);
            return ResponseEntity.ok(ApiResponse.success("Resource rejected", resource));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}