package com.enicconnect.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "resources")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Resource {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 200)
    private String title;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "resource_type", nullable = false)
    private ResourceType resourceType;
    
    @ManyToOne
    @JoinColumn(name = "subject_id")
    private Subject subject;
    
    @ManyToOne
    @JoinColumn(name = "uploaded_by_user_id", nullable = false)
    private User uploadedBy;
    
    @Column(name = "file_url", nullable = false, length = 255)
    private String fileUrl;
    
    @Column(name = "file_size_bytes")
    private Long fileSizeBytes;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @Column(name = "average_rating", nullable = false, precision = 3, scale = 2)
    private BigDecimal averageRating = BigDecimal.ZERO;
    
    @Column(name = "download_count", nullable = false)
    private Integer downloadCount = 0;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ResourceStatus status = ResourceStatus.PENDING;
    
    @ManyToOne
    @JoinColumn(name = "reviewed_by_professor_id")
    private Professor reviewedBy;
    
    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
    
    public enum ResourceType {
        COURSE, TD, EXAM, SUMMARY
    }
    
    public enum ResourceStatus {
        PENDING, APPROVED, REJECTED
    }
}