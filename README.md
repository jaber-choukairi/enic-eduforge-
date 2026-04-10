ENIC-Connect + EduForge

# Setup Instructions

## Backend (Spring Boot)

1. Install dependencies: `mvn clean install`
2. Set environment variables:
   ```
   export DB_USERNAME=your_db_user
   export DB_PASSWORD=your_db_pass
   ```
   Or copy example files:
   ```
   cp backend/src/main/resources/application-dev.example.properties backend/src/main/resources/application-dev.properties
   # Edit with your credentials
   ```
3. Run:
   ```
   mvn spring-boot:run -Dspring-boot.run.profiles=dev
   ```
   Access API at http://localhost:8080/api

Note: application-*.properties (except application.properties) are gitignored for security. Use .example files as templates.

## Profiles
- `dev`: Development with CORS *
- `aiven`: Production Aiven MySQL
