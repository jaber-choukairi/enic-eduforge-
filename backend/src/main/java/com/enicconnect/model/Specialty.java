package com.enicconnect.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import javax.persistence.*;

@Entity
@Table(name = "specialties")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Specialty {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, unique = true)
    private SpecialtyCode code;
    
    @Column(nullable = false, unique = true, length = 100)
    private String name;
    
    public enum SpecialtyCode {
        AI, CYBER, DATA, CLOUD, WEB, SOFTWARE
    }
}