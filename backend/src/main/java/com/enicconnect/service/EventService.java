package com.enicconnect.service;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class EventService {
    
    private final EventRepository eventRepository;
    private final ClubRepository clubRepository;
    private final UserRepository userRepository;
    
    @Transactional
    public Event createEvent(String title, Event.EventType eventType, String description,
                             String location, LocalDateTime startDatetime, LocalDateTime endDatetime,
                             Integer maxParticipants, Long clubId, Long createdByUserId) {
        
        User createdBy = userRepository.findById(createdByUserId)
            .orElseThrow(() -> new RuntimeException("User not found"));
        
        Club club = null;
        if (clubId != null) {
            club = clubRepository.findById(clubId)
                .orElseThrow(() -> new RuntimeException("Club not found"));
        }
        
        Event event = Event.builder()
            .title(title)
            .eventType(eventType)
            .description(description)
            .location(location)
            .startDatetime(startDatetime)
            .endDatetime(endDatetime)
            .maxParticipants(maxParticipants)
            .club(club)
            .createdBy(createdBy)
            .build();
        
        return eventRepository.save(event);
    }
    
    @Transactional
    public Event updateEvent(Long eventId, String title, String description, 
                             String location, LocalDateTime startDatetime, 
                             LocalDateTime endDatetime, Integer maxParticipants) {
        
        Event event = getEventById(eventId);
        
        if (title != null) event.setTitle(title);
        if (description != null) event.setDescription(description);
        if (location != null) event.setLocation(location);
        if (startDatetime != null) event.setStartDatetime(startDatetime);
        if (endDatetime != null) event.setEndDatetime(endDatetime);
        if (maxParticipants != null) event.setMaxParticipants(maxParticipants);
        
        return eventRepository.save(event);
    }
    
    @Transactional
    public void deleteEvent(Long eventId) {
        eventRepository.deleteById(eventId);
    }
    
    public Event getEventById(Long id) {
        return eventRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Event not found with id: " + id));
    }
    
    public List<Event> getUpcomingEvents() {
        return eventRepository.findUpcomingEvents(LocalDateTime.now());
    }
    
    public List<Event> getPastEvents() {
        return eventRepository.findPastEvents(LocalDateTime.now());
    }
    
    public List<Event> getEventsByType(Event.EventType type) {
        return eventRepository.findByEventType(type);
    }
    
    public List<Event> getEventsByClub(Long clubId) {
        return eventRepository.findByClubId(clubId);
    }
    
    public List<Event> getAllEvents() {
        return eventRepository.findAll();
    }
}