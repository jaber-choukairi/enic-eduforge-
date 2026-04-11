package com.enicconnect.service;

import com.enicconnect.model.User;
import com.enicconnect.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserService {
    
    private final UserRepository userRepository;
    
    @Transactional
    public User createUser(String firstName, String lastName, String email, 
                           String passwordHash, User.UserRole role) {
        if (userRepository.existsByEmail(email)) {
            throw new RuntimeException("Email already exists: " + email);
        }
        
        User user = User.builder()
            .firstName(firstName)
            .lastName(lastName)
            .email(email)
            .passwordHash(passwordHash)
            .role(role)
            .isActive(true)
            .build();
        
        return userRepository.save(user);
    }
    
    @Transactional
    public User updateUser(Long userId, String firstName, String lastName, String email) {
        User user = getUserById(userId);
        user.setFirstName(firstName);
        user.setLastName(lastName);
        user.setEmail(email);
        return userRepository.save(user);
    }
    
    @Transactional
    public void deactivateUser(Long userId) {
        User user = getUserById(userId);
        user.setIsActive(false);
        userRepository.save(user);
    }
    
    @Transactional
    public void activateUser(Long userId) {
        User user = getUserById(userId);
        user.setIsActive(true);
        userRepository.save(user);
    }
    
    public User getUserById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("User not found with id: " + id));
    }
    
    public Optional<User> getUserByEmail(String email) {
        return userRepository.findByEmail(email);
    }
    
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }
    
    public List<User> getUsersByRole(User.UserRole role) {
        return userRepository.findByRole(role);
    }
    
    public boolean validateUserCredentials(String email, String passwordHash) {
        Optional<User> user = userRepository.findByEmail(email);
        return user.isPresent() && user.get().getPasswordHash().equals(passwordHash);
    }
}