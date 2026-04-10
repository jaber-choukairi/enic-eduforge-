package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ResourceService {
    
    private final ResourceRepository resourceRepository;
    private final UserRepository userRepository;
    private final SubjectRepository subjectRepository;
    private final ProfessorRepository professorRepository;
    
    @Transactional
    public Resource uploadResource(String title, Resource.ResourceType resourceType, 
                                    Long subjectId, Long uploadedByUserId, String fileUrl,
                                    Long fileSizeBytes, String description) {
        
        User uploadedBy = userRepository.findById(uploadedByUserId)
            .orElseThrow(() -> new RuntimeException("User not found"));
        
        Subject subject = null;
        if (subjectId != null) {
            subject = subjectRepository.findById(subjectId)
                .orElseThrow(() -> new RuntimeException("Subject not found"));
        }
        
        Resource resource = Resource.builder()
            .title(title)
            .resourceType(resourceType)
            .subject(subject)
            .uploadedBy(uploadedBy)
            .fileUrl(fileUrl)
            .fileSizeBytes(fileSizeBytes)
            .description(description)
            .averageRating(BigDecimal.ZERO)
            .downloadCount(0)
            .status(Resource.ResourceStatus.PENDING)
            .build();
        
        return resourceRepository.save(resource);
    }
    
    @Transactional
    public Resource approveResource(Long resourceId, Long professorId) {
        Resource resource = getResourceById(resourceId);
        Professor professor = professorRepository.findById(professorId)
            .orElseThrow(() -> new RuntimeException("Professor not found"));
        
        resource.setStatus(Resource.ResourceStatus.APPROVED);
        resource.setReviewedBy(professor);
        resource.setReviewedAt(LocalDateTime.now());
        
        return resourceRepository.save(resource);
    }
    
    @Transactional
    public Resource rejectResource(Long resourceId, Long professorId) {
        Resource resource = getResourceById(resourceId);
        Professor professor = professorRepository.findById(professorId)
            .orElseThrow(() -> new RuntimeException("Professor not found"));
        
        resource.setStatus(Resource.ResourceStatus.REJECTED);
        resource.setReviewedBy(professor);
        resource.setReviewedAt(LocalDateTime.now());
        
        return resourceRepository.save(resource);
    }
    
    @Transactional
    public void incrementDownloadCount(Long resourceId) {
        Resource resource = getResourceById(resourceId);
        resource.setDownloadCount(resource.getDownloadCount() + 1);
        resourceRepository.save(resource);
    }
    
    @Transactional
    public void updateRating(Long resourceId, BigDecimal newAverageRating) {
        Resource resource = getResourceById(resourceId);
        resource.setAverageRating(newAverageRating);
        resourceRepository.save(resource);
    }
    
    public Resource getResourceById(Long id) {
        return resourceRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Resource not found with id: " + id));
    }
    
    public List<Resource> getAllApprovedResources() {
        return resourceRepository.findApprovedResources();
    }
    
    public List<Resource> getResourcesByType(Resource.ResourceType type) {
        return resourceRepository.findByResourceType(type);
    }
    
    public List<Resource> getResourcesBySubject(Long subjectId) {
        return resourceRepository.findApprovedResourcesBySubject(subjectId);
    }
    
    public List<Resource> getPendingResources() {
        return resourceRepository.findByStatus(Resource.ResourceStatus.PENDING);
    }
    
    public List<Resource> getResourcesByUploader(Long userId) {
        return resourceRepository.findByUploadedById(userId);
    }
}