package com.enicconnect.repository;

import com.enicconnect.model.Event;
import com.enicconnect.model.Event.EventType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface EventRepository extends JpaRepository<Event, Long> {
    
    List<Event> findByEventType(EventType eventType);
    
    List<Event> findByClubId(Long clubId);
    
    List<Event> findByCreatedById(Long userId);
    
    @Query("SELECT e FROM Event e WHERE e.startDatetime >= :now ORDER BY e.startDatetime ASC")
    List<Event> findUpcomingEvents(@Param("now") LocalDateTime now);
    
    @Query("SELECT e FROM Event e WHERE e.startDatetime BETWEEN :start AND :end")
    List<Event> findEventsBetween(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);
    
    @Query("SELECT e FROM Event e WHERE e.startDatetime < :now ORDER BY e.startDatetime DESC")
    List<Event> findPastEvents(@Param("now") LocalDateTime now);
}