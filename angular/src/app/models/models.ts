export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface LoginRequest { email: string; password: string; }

export interface LoginResponse {
  userId: number; email: string; firstName: string; lastName: string;
  role: 'STUDENT' | 'PROFESSOR' | 'CHAIR';
  studentId?: number; professorId?: number;
  specialty?: string; riskScore?: number; riskLevel?: string;
  department?: string; message: string;
}

export interface RegisterRequest {
  firstName: string; lastName: string; email: string; password: string;
  role: string; specialtyId?: number; academicLevel?: string;
  groupName?: string; enrollmentYear?: number; currentSemester?: number;
  department?: string; officeEmail?: string;
}

export interface Student {
  id: number; academicLevel: string; groupName: string;
  riskScore: number; riskLevel: string;
  user: { firstName: string; lastName: string; email: string; };
  specialty: { name: string; code: string; } | null;
}

export interface Grade {
  id: number; gradeType: string; gradeValue: number;
  comment: string; academicYear: string;
  subject: { id: number; name: string; } | null;
  student: { id: number; } | null;
  professor: { id: number; } | null;
}

export interface GradeDTO {
  studentId: number; subjectId: number; gradeType: string;
  gradeValue: number; comment: string; academicYear: string;
}

export interface Event {
  id: number; title: string; eventType: string;
  description: string; location: string;
  startDatetime: string; endDatetime: string;
  maxParticipants: number; currentParticipants: number;
  isActive: boolean;
}

export interface EventDTO {
  title: string; eventType: string; description: string;
  location: string; startDatetime: string; endDatetime: string;
  maxParticipants: number; clubId?: number;
}

export interface Resource {
  id: number; title: string; resourceType: string;
  fileUrl: string; description: string; status: string;
  downloadCount: number; fileSizeBytes: number;
  subject: { id: number; name: string; } | null;
  uploadedBy: { firstName: string; lastName: string; } | null;
}

export interface ResourceDTO {
  title: string; resourceType: string; subjectId: number;
  fileUrl: string; fileSizeBytes: number; description: string;
}

export interface Subject { id: number; name: string; credits: number; }
export interface Specialty { id: number; name: string; code: string; }

export interface StudentDashboard {
  studentId: number; firstName: string; lastName: string;
  academicLevel: string; specialty: string;
  averageGrade: number; riskScore: number; riskLevel: string;
  recentGrades: Grade[]; totalGrades: number;
}

export interface ProfessorDashboard {
  professorId: number; name: string; department: string;
  averageGradeGiven: number; pendingResourcesCount: number;
  atRiskStudentsCount: number; atRiskStudents: Student[];
}
export interface LoginResponse {
  userId: number; email: string; firstName: string; lastName: string;
  role: 'STUDENT' | 'PROFESSOR' | 'CHAIR';
  studentId?: number; professorId?: number;
  specialty?: string; riskScore?: number; riskLevel?: string;
  academicLevel?: string;  // ← ajouter cette ligne
  department?: string; message: string;
}