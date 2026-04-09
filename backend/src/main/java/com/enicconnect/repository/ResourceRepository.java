package com.enicconnect.repository;

import com.enicconnect.model.Resource;
import com.enicconnect.model.Resource.ResourceStatus;
import com.enicconnect.model.Resource.ResourceType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ResourceRepository extends JpaRepository<Resource, Long> {
    
    List<Resource> findByStatus(ResourceStatus status);
    
    List<Resource> findByResourceType(ResourceType resourceType);
    
    List<Resource> findBySubjectId(Long subjectId);
    
    List<Resource> findByUploadedById(Long userId);
    
    @Query("SELECT r FROM Resource r WHERE r.status = 'APPROVED' ORDER BY r.createdAt DESC")
    List<Resource> findApprovedResources();
    
    @Query("SELECT r FROM Resource r WHERE r.subject.id = :subjectId AND r.status = 'APPROVED'")
    List<Resource> findApprovedResourcesBySubject(@Param("subjectId") Long subjectId);
}