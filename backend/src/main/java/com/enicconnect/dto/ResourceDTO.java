package com.enicconnect.dto;

import com.enicconnect.model.Resource;
import lombok.Data;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Data
public class ResourceDTO {
    
    @NotBlank(message = "Title is required")
    private String title;
    
    @NotNull(message = "Resource type is required")
    private Resource.ResourceType resourceType;
    
    private Long subjectId;
    
    @NotBlank(message = "File URL is required")
    private String fileUrl;
    
    private Long fileSizeBytes;
    
    private String description;
}