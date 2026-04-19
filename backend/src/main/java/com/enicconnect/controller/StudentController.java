package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.model.Grade;
import com.enicconnect.model.Student;
import com.enicconnect.service.GradeService;
import com.enicconnect.service.StudentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/students")
@RequiredArgsConstructor
public class StudentController {
    
    private final StudentService studentService;
    private final GradeService gradeService;
    
    @GetMapping("/{studentId}/dashboard")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getStudentDashboard(@PathVariable Long studentId) {
        try {
            Student student = studentService.getStudentById(studentId);
            BigDecimal averageGrade = studentService.getStudentAverageGrade(studentId);
            List<Grade> recentGrades = gradeService.getRecentGrades(studentId);
            
            Map<String, Object> dashboard = new HashMap<>();
            dashboard.put("studentId", student.getId());
            dashboard.put("firstName", student.getUser().getFirstName());
            dashboard.put("lastName", student.getUser().getLastName());
            dashboard.put("academicLevel", student.getAcademicLevel());
            dashboard.put("specialty", student.getSpecialty() != null ? student.getSpecialty().getName() : null);
            dashboard.put("averageGrade", averageGrade);
            dashboard.put("riskScore", student.getRiskScore());
            dashboard.put("riskLevel", student.getRiskLevel());
            dashboard.put("recentGrades", recentGrades);
            dashboard.put("totalGrades", recentGrades.size());
            
            return ResponseEntity.ok(ApiResponse.success(dashboard));
            
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{studentId}/grades")
    public ResponseEntity<ApiResponse<List<Grade>>> getStudentGrades(@PathVariable Long studentId) {
        try {
            List<Grade> grades = gradeService.getStudentGrades(studentId);
            return ResponseEntity.ok(ApiResponse.success(grades));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{studentId}/average")
    public ResponseEntity<ApiResponse<BigDecimal>> getStudentAverage(@PathVariable Long studentId) {
        try {
            BigDecimal average = studentService.getStudentAverageGrade(studentId);
            return ResponseEntity.ok(ApiResponse.success(average));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/risk")
    public ResponseEntity<ApiResponse<List<Student>>> getStudentsAtRisk() {
        try {
            List<Student> atRiskStudents = studentService.getStudentsAtRisk();
            return ResponseEntity.ok(ApiResponse.success(atRiskStudents));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/specialty/{specialtyId}")
    public ResponseEntity<ApiResponse<List<Student>>> getStudentsBySpecialty(@PathVariable Long specialtyId) {
        try {
            List<Student> students = studentService.getStudentsBySpecialty(specialtyId);
            return ResponseEntity.ok(ApiResponse.success(students));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/{studentId}/update-risk")
    public ResponseEntity<ApiResponse<Void>> updateRiskScore(@PathVariable Long studentId) {
        try {
            studentService.updateRiskScore(studentId);
            return ResponseEntity.ok(ApiResponse.success("Risk score updated successfully", null));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}