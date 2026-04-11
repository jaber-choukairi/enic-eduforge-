package com.enicconnect;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class EnicConnectApplication {
    public static void main(String[] args) {
        SpringApplication.run(EnicConnectApplication.class, args);
        System.out.println("╔════════════════════════════════════════╗");
        System.out.println("║     ENIC CONNECT BACKEND STARTED       ║");
        System.out.println("║     http://localhost:8080/api/health          ║");
        System.out.println("╚════════════════════════════════════════╝");
    }
}
