package com.enicconnect.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.sql.DataSource;
import java.sql.Connection;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/health")
public class HealthController {

    @Autowired(required = false)
    private DataSource dataSource;

    @GetMapping
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> status = new HashMap<>();
        status.put("status", "UP");
        status.put("service", "ENIC Connect API");
        status.put("version", "2.0.0");
        status.put("timestamp", System.currentTimeMillis());

        // Check DB connectivity
        if (dataSource != null) {
            try (Connection conn = dataSource.getConnection()) {
                status.put("database", "CONNECTED");
                status.put("dbUrl", conn.getMetaData().getURL());
            } catch (Exception e) {
                status.put("database", "DISCONNECTED");
                status.put("dbError", e.getMessage());
            }
        }
        return ResponseEntity.ok(status);
    }

    @GetMapping("/ping")
    public ResponseEntity<String> ping() {
        return ResponseEntity.ok("pong");
    }
}
