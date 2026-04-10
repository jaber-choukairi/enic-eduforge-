package com.enicconnect.config;

import com.enicconnect.model.*;
import com.enicconnect.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Component
@RequiredArgsConstructor
public class DatabaseInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final SpecialtyRepository specialtyRepository;
    private final StudentRepository studentRepository;
    private final ProfessorRepository professorRepository;
    private final SubjectRepository subjectRepository;
    private final EventRepository eventRepository;
    private final ResourceRepository resourceRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) throws Exception {

        // ── Specialties ────────────────────────────────────────
        if (specialtyRepository.count() == 0) {
            System.out.println("📚 Initializing specialties...");
            for (Specialty.SpecialtyCode code : Specialty.SpecialtyCode.values()) {
                Specialty s = new Specialty();
                s.setCode(code);
                s.setName(getSpecialtyName(code));
                specialtyRepository.save(s);
            }
        }

        // ── Demo Users ─────────────────────────────────────────
        if (userRepository.count() == 0) {
            System.out.println("👥 Creating demo users...");
            final String PASS = passwordEncoder.encode("demo123");

            // Student — Ahmed
            User studentUser = User.builder()
                .firstName("Ahmed").lastName("Ben Salem")
                .email("ahmed.ben@enic.edu.tn")
                .passwordHash(PASS).role(User.UserRole.STUDENT).isActive(true).build();
            userRepository.save(studentUser);

            // Student 2 — Sara
            User studentUser2 = User.builder()
                .firstName("Sara").lastName("Khalil")
                .email("sara.khalil@enic.edu.tn")
                .passwordHash(PASS).role(User.UserRole.STUDENT).isActive(true).build();
            userRepository.save(studentUser2);

            // Student 3 — Rami (at-risk)
            User studentUser3 = User.builder()
                .firstName("Rami").lastName("Mekni")
                .email("rami.mekni@enic.edu.tn")
                .passwordHash(PASS).role(User.UserRole.STUDENT).isActive(true).build();
            userRepository.save(studentUser3);

            // Professor — Mehdi
            User profUser = User.builder()
                .firstName("Mehdi").lastName("Cherif")
                .email("mehdi.cherif@enic.edu.tn")
                .passwordHash(PASS).role(User.UserRole.PROFESSOR).isActive(true).build();
            userRepository.save(profUser);

            // Chair — Lina
            User chairUser = User.builder()
                .firstName("Lina").lastName("Slim")
                .email("lina.slim@enic.edu.tn")
                .passwordHash(PASS).role(User.UserRole.CHAIR).isActive(true).build();
            userRepository.save(chairUser);

            // ── Student profiles ───────────────────────────────
            Specialty ai = specialtyRepository.findByCode(Specialty.SpecialtyCode.AI).orElse(null);
            Specialty cyber = specialtyRepository.findByCode(Specialty.SpecialtyCode.CYBER).orElse(null);

            if (ai != null) {
                studentRepository.save(Student.builder()
                    .user(studentUser).specialty(ai)
                    .academicLevel("L3").groupName("IA3-A")
                    .enrollmentYear((short) 2023).currentSemester((byte) 5)
                    .riskScore(BigDecimal.valueOf(20.00)).riskLevel(Student.RiskLevel.STABLE)
                    .build());

                studentRepository.save(Student.builder()
                    .user(studentUser2).specialty(ai)
                    .academicLevel("L3").groupName("IA3-A")
                    .enrollmentYear((short) 2023).currentSemester((byte) 5)
                    .riskScore(BigDecimal.valueOf(38.00)).riskLevel(Student.RiskLevel.ATTENTION_REQUIRED)
                    .build());
            }

            if (cyber != null) {
                studentRepository.save(Student.builder()
                    .user(studentUser3).specialty(cyber)
                    .academicLevel("L2").groupName("CY2-B")
                    .enrollmentYear((short) 2024).currentSemester((byte) 3)
                    .riskScore(BigDecimal.valueOf(72.00)).riskLevel(Student.RiskLevel.HIGH_RISK)
                    .build());
            }

            // ── Professor profiles ─────────────────────────────
            Professor prof = Professor.builder()
                .user(profUser).department("Intelligence Artificielle")
                .officeEmail("mehdi.cherif@enic.edu.tn").build();
            professorRepository.save(prof);

            Professor chair = Professor.builder()
                .user(chairUser).department("Tech Club ENIC")
                .officeEmail("lina.slim@enic.edu.tn").build();
            professorRepository.save(chair);

            System.out.println("✅ Demo accounts created:");
            System.out.println("   Student  : ahmed.ben@enic.edu.tn   / demo123");
            System.out.println("   Professor: mehdi.cherif@enic.edu.tn / demo123");
            System.out.println("   Chair    : lina.slim@enic.edu.tn   / demo123");
        }

        // ── Subjects ───────────────────────────────────────────
        if (subjectRepository.count() == 0) {
            System.out.println("📖 Initializing subjects...");
            Specialty ai = specialtyRepository.findByCode(Specialty.SpecialtyCode.AI).orElse(null);

            Subject[] subjects = {
                Subject.builder().code("ALGO301").name("Algorithmes Avancés")
                    .coefficient(BigDecimal.valueOf(3.00)).specialty(ai).academicLevel("L3").semester((byte) 5).isCore(true).build(),
                Subject.builder().code("ML301").name("Machine Learning")
                    .coefficient(BigDecimal.valueOf(4.00)).specialty(ai).academicLevel("L3").semester((byte) 5).isCore(true).build(),
                Subject.builder().code("MATH301").name("Mathématiques")
                    .coefficient(BigDecimal.valueOf(3.00)).specialty(ai).academicLevel("L3").semester((byte) 5).isCore(true).build(),
                Subject.builder().code("CV301").name("Vision par Ordinateur")
                    .coefficient(BigDecimal.valueOf(3.00)).specialty(ai).academicLevel("L3").semester((byte) 5).isCore(false).build(),
                Subject.builder().code("NLP301").name("NLP & Transformers")
                    .coefficient(BigDecimal.valueOf(3.00)).specialty(ai).academicLevel("L3").semester((byte) 6).isCore(false).build(),
                Subject.builder().code("STAT301").name("Statistiques")
                    .coefficient(BigDecimal.valueOf(2.00)).specialty(ai).academicLevel("L3").semester((byte) 5).isCore(false).build()
            };
            for (Subject s : subjects) subjectRepository.save(s);
        }

        // ── Sample Events ──────────────────────────────────────
        if (eventRepository.count() == 0) {
            System.out.println("📅 Creating sample events...");
            User chair = userRepository.findByEmail("lina.slim@enic.edu.tn").orElse(null);

            if (chair != null) {
                eventRepository.save(Event.builder()
                    .title("Hackathon IA ENIC 2025")
                    .eventType(Event.EventType.HACKATHON)
                    .description("48h de compétition pour résoudre des problèmes réels avec l'IA. Équipes de 3-4 étudiants.")
                    .location("Salle Innovation – ENIC Carthage")
                    .startDatetime(LocalDateTime.now().plusDays(14))
                    .endDatetime(LocalDateTime.now().plusDays(16))
                    .maxParticipants(80)
                    .createdBy(chair).build());

                eventRepository.save(Event.builder()
                    .title("Conférence: L'IA Générative en Entreprise")
                    .eventType(Event.EventType.CONFERENCE)
                    .description("Retour d'expérience de professionnels sur l'intégration de l'IA générative dans les entreprises tunisiennes.")
                    .location("Amphithéâtre A – ENIC")
                    .startDatetime(LocalDateTime.now().plusDays(7))
                    .endDatetime(LocalDateTime.now().plusDays(7).plusHours(3))
                    .maxParticipants(200)
                    .createdBy(chair).build());

                eventRepository.save(Event.builder()
                    .title("Workshop: MLOps avec Docker & Kubernetes")
                    .eventType(Event.EventType.WORKSHOP)
                    .description("Atelier pratique sur le déploiement de modèles ML en production.")
                    .location("Labo Informatique – B204")
                    .startDatetime(LocalDateTime.now().plusDays(21))
                    .endDatetime(LocalDateTime.now().plusDays(21).plusHours(4))
                    .maxParticipants(30)
                    .createdBy(chair).build());

                eventRepository.save(Event.builder()
                    .title("Networking: Rencontre Entreprises & Étudiants")
                    .eventType(Event.EventType.NETWORKING)
                    .description("Rencontrez des recruteurs d'Ooredoo, Telnet, Vermeg et Sofrecom.")
                    .location("Hall Principal – ENIC")
                    .startDatetime(LocalDateTime.now().plusDays(30))
                    .endDatetime(LocalDateTime.now().plusDays(30).plusHours(2))
                    .maxParticipants(150)
                    .createdBy(chair).build());
            }
        }

        // ── Sample Resources ───────────────────────────────────
        if (resourceRepository.count() == 0) {
            System.out.println("📁 Creating sample resources...");
            User prof = userRepository.findByEmail("mehdi.cherif@enic.edu.tn").orElse(null);
            Subject ml = subjectRepository.findByCode("ML301").orElse(null);
            Subject nlp = subjectRepository.findByCode("NLP301").orElse(null);
            Subject stat = subjectRepository.findByCode("STAT301").orElse(null);

            if (prof != null) {
                Professor professor = professorRepository.findByUserId(prof.getId()).orElse(null);

                resourceRepository.save(Resource.builder()
                    .title("Cours Machine Learning – Chapitre 1: Régression")
                    .resourceType(Resource.ResourceType.COURSE)
                    .subject(ml).uploadedBy(prof)
                    .fileUrl("https://example.com/files/ml-ch1.pdf")
                    .fileSizeBytes(2048000L)
                    .description("Introduction à la régression linéaire et logistique avec exemples pratiques.")
                    .averageRating(BigDecimal.valueOf(4.5))
                    .downloadCount(127)
                    .status(Resource.ResourceStatus.APPROVED)
                    .reviewedBy(professor).reviewedAt(LocalDateTime.now().minusDays(5))
                    .build());

                resourceRepository.save(Resource.builder()
                    .title("TD Machine Learning – Arbres de Décision & Random Forest")
                    .resourceType(Resource.ResourceType.TD)
                    .subject(ml).uploadedBy(prof)
                    .fileUrl("https://example.com/files/ml-td-dt.pdf")
                    .fileSizeBytes(512000L)
                    .description("10 exercices progressifs sur les arbres de décision avec corrections.")
                    .averageRating(BigDecimal.valueOf(4.8))
                    .downloadCount(89)
                    .status(Resource.ResourceStatus.APPROVED)
                    .reviewedBy(professor).reviewedAt(LocalDateTime.now().minusDays(3))
                    .build());

                resourceRepository.save(Resource.builder()
                    .title("Examen ML 2023-2024 avec Corrections")
                    .resourceType(Resource.ResourceType.EXAM)
                    .subject(ml).uploadedBy(prof)
                    .fileUrl("https://example.com/files/ml-exam-2024.pdf")
                    .fileSizeBytes(768000L)
                    .description("Examen final avec corrections détaillées.")
                    .averageRating(BigDecimal.valueOf(4.9))
                    .downloadCount(203)
                    .status(Resource.ResourceStatus.APPROVED)
                    .reviewedBy(professor).reviewedAt(LocalDateTime.now().minusDays(10))
                    .build());

                resourceRepository.save(Resource.builder()
                    .title("Résumé NLP – Attention Mechanism & Transformers")
                    .resourceType(Resource.ResourceType.SUMMARY)
                    .subject(nlp).uploadedBy(prof)
                    .fileUrl("https://example.com/files/nlp-summary.pdf")
                    .fileSizeBytes(384000L)
                    .description("Fiche récapitulative du mécanisme d'attention et architecture Transformer.")
                    .averageRating(BigDecimal.valueOf(4.7))
                    .downloadCount(156)
                    .status(Resource.ResourceStatus.APPROVED)
                    .reviewedBy(professor).reviewedAt(LocalDateTime.now().minusDays(7))
                    .build());

                resourceRepository.save(Resource.builder()
                    .title("TD Statistiques – Tests d'Hypothèse")
                    .resourceType(Resource.ResourceType.TD)
                    .subject(stat).uploadedBy(prof)
                    .fileUrl("https://example.com/files/stat-td-hypothesis.pdf")
                    .fileSizeBytes(256000L)
                    .description("8 exercices sur les tests d'hypothèse et intervalles de confiance.")
                    .averageRating(BigDecimal.valueOf(4.3))
                    .downloadCount(74)
                    .status(Resource.ResourceStatus.APPROVED)
                    .reviewedBy(professor).reviewedAt(LocalDateTime.now().minusDays(2))
                    .build());

                // Pending resource (student contribution)
                User student = userRepository.findByEmail("ahmed.ben@enic.edu.tn").orElse(null);
                if (student != null) {
                    resourceRepository.save(Resource.builder()
                        .title("TD Backpropagation – Réseau de Neurones")
                        .resourceType(Resource.ResourceType.TD)
                        .subject(ml).uploadedBy(student)
                        .fileUrl("https://example.com/files/student-bp-td.pdf")
                        .fileSizeBytes(195000L)
                        .description("TD personnel sur la rétropropagation avec exemples pas-à-pas.")
                        .averageRating(BigDecimal.ZERO)
                        .downloadCount(0)
                        .status(Resource.ResourceStatus.PENDING)
                        .build());
                }
            }
        }

        System.out.println("🎉 ENIC Connect database initialized successfully!");
    }

    private String getSpecialtyName(Specialty.SpecialtyCode code) {
        switch (code) {
            case AI: return "Intelligence Artificielle";
            case CYBER: return "Cybersécurité";
            case DATA: return "Data Science";
            case CLOUD: return "Cloud Computing";
            case WEB: return "Développement Web";
            case SOFTWARE: return "Génie Logiciel";
            default: return code.name();
        }
    }
}
