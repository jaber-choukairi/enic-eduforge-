package com.enicconnect.dto;

import com.enicconnect.model.User;
import lombok.Data;
import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Data
public class RegisterRequest {

    @NotBlank(message = "First name is required")
    private String firstName;

    @NotBlank(message = "Last name is required")
    private String lastName;

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;

    @NotBlank(message = "Password is required")
    private String password;

    @NotNull(message = "Role is required")
    private User.UserRole role;

    // Student specific fields
    private Long specialtyId;
    private String academicLevel;
    private String groupName;
    private Integer enrollmentYear;   // Integer (not Short) to avoid JSON parse issues
    private Integer currentSemester;  // Integer (not Byte) to avoid JSON parse issues

    // Professor specific fields
    private String department;
    private String officeEmail;

    public Short getEnrollmentYearAsShort() {
        return enrollmentYear != null ? enrollmentYear.shortValue() : null;
    }

    public Byte getCurrentSemesterAsByte() {
        return currentSemester != null ? currentSemester.byteValue() : null;
    }
}
