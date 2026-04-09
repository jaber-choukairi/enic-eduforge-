package com.enicconnect.dto;

import com.enicconnect.model.Event;
import lombok.Data;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Data
public class EventDTO {
    
    @NotBlank(message = "Title is required")
    private String title;
    
    @NotNull(message = "Event type is required")
    private Event.EventType eventType;
    
    private String description;
    
    private String location;
    
    @NotNull(message = "Start date/time is required")
    private LocalDateTime startDatetime;
    
    private LocalDateTime endDatetime;
    
    private Integer maxParticipants;
    
    private Long clubId;
}