package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.dto.ResourceDTO;
import com.enicconnect.model.Resource;
import com.enicconnect.service.ResourceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/resources")
@RequiredArgsConstructor
public class ResourceController {
    
    private final ResourceService resourceService;
    
    @GetMapping
    public ResponseEntity<ApiResponse<List<Resource>>> getAllResources() {
        try {
            List<Resource> resources = resourceService.getAllApprovedResources();
            return ResponseEntity.ok(ApiResponse.success(resources));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{resourceId}")
    public ResponseEntity<ApiResponse<Resource>> getResourceById(@PathVariable Long resourceId) {
        try {
            Resource resource = resourceService.getResourceById(resourceId);
            return ResponseEntity.ok(ApiResponse.success(resource));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/upload")
    public ResponseEntity<ApiResponse<Resource>> uploadResource(@Valid @RequestBody ResourceDTO resourceDTO,
                                                                  @RequestParam Long userId) {
        try {
            Resource resource = resourceService.uploadResource(
                resourceDTO.getTitle(),
                resourceDTO.getResourceType(),
                resourceDTO.getSubjectId(),
                userId,
                resourceDTO.getFileUrl(),
                resourceDTO.getFileSizeBytes(),
                resourceDTO.getDescription()
            );
            return ResponseEntity.ok(ApiResponse.success("Resource uploaded successfully", resource));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/type/{type}")
    public ResponseEntity<ApiResponse<List<Resource>>> getResourcesByType(@PathVariable String type) {
        try {
            Resource.ResourceType resourceType = Resource.ResourceType.valueOf(type.toUpperCase());
            List<Resource> resources = resourceService.getResourcesByType(resourceType);
            return ResponseEntity.ok(ApiResponse.success(resources));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error("Invalid resource type"));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/subject/{subjectId}")
    public ResponseEntity<ApiResponse<List<Resource>>> getResourcesBySubject(@PathVariable Long subjectId) {
        try {
            List<Resource> resources = resourceService.getResourcesBySubject(subjectId);
            return ResponseEntity.ok(ApiResponse.success(resources));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/{resourceId}/download")
    public ResponseEntity<ApiResponse<Void>> incrementDownloadCount(@PathVariable Long resourceId) {
        try {
            resourceService.incrementDownloadCount(resourceId);
            return ResponseEntity.ok(ApiResponse.success("Download count incremented", null));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}