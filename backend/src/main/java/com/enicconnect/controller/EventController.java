package com.enicconnect.controller;

import com.enicconnect.dto.ApiResponse;
import com.enicconnect.dto.EventDTO;
import com.enicconnect.model.Event;
import com.enicconnect.service.EventService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/events")
@RequiredArgsConstructor
public class EventController {
    
    private final EventService eventService;
    
    @GetMapping
    public ResponseEntity<ApiResponse<List<Event>>> getAllEvents() {
        try {
            List<Event> events = eventService.getAllEvents();
            return ResponseEntity.ok(ApiResponse.success(events));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/upcoming")
    public ResponseEntity<ApiResponse<List<Event>>> getUpcomingEvents() {
        try {
            List<Event> events = eventService.getUpcomingEvents();
            return ResponseEntity.ok(ApiResponse.success(events));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/{eventId}")
    public ResponseEntity<ApiResponse<Event>> getEventById(@PathVariable Long eventId) {
        try {
            Event event = eventService.getEventById(eventId);
            return ResponseEntity.ok(ApiResponse.success(event));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PostMapping("/create")
    public ResponseEntity<ApiResponse<Event>> createEvent(@Valid @RequestBody EventDTO eventDTO,
                                                           @RequestParam Long userId) {
        try {
            Event event = eventService.createEvent(
                eventDTO.getTitle(),
                eventDTO.getEventType(),
                eventDTO.getDescription(),
                eventDTO.getLocation(),
                eventDTO.getStartDatetime(),
                eventDTO.getEndDatetime(),
                eventDTO.getMaxParticipants(),
                eventDTO.getClubId(),
                userId
            );
            return ResponseEntity.ok(ApiResponse.success("Event created successfully", event));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @PutMapping("/{eventId}")
    public ResponseEntity<ApiResponse<Event>> updateEvent(@PathVariable Long eventId,
                                                           @RequestBody EventDTO eventDTO) {
        try {
            Event event = eventService.updateEvent(
                eventId,
                eventDTO.getTitle(),
                eventDTO.getDescription(),
                eventDTO.getLocation(),
                eventDTO.getStartDatetime(),
                eventDTO.getEndDatetime(),
                eventDTO.getMaxParticipants()
            );
            return ResponseEntity.ok(ApiResponse.success("Event updated successfully", event));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @DeleteMapping("/{eventId}")
    public ResponseEntity<ApiResponse<Void>> deleteEvent(@PathVariable Long eventId) {
        try {
            eventService.deleteEvent(eventId);
            return ResponseEntity.ok(ApiResponse.success("Event deleted successfully", null));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
    
    @GetMapping("/type/{type}")
    public ResponseEntity<ApiResponse<List<Event>>> getEventsByType(@PathVariable String type) {
        try {
            Event.EventType eventType = Event.EventType.valueOf(type.toUpperCase());
            List<Event> events = eventService.getEventsByType(eventType);
            return ResponseEntity.ok(ApiResponse.success(events));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error("Invalid event type"));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}