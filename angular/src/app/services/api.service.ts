import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ApiResponse, LoginRequest, LoginResponse, RegisterRequest,
  Student, Grade, GradeDTO, Event, EventDTO, Resource, ResourceDTO,
  Subject, Specialty, StudentDashboard, ProfessorDashboard
} from '../models/models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = '/api';

  constructor(private http: HttpClient) {}

  // ── AUTH ──────────────────────────────────────────────────────────────────
  login(body: LoginRequest): Observable<ApiResponse<LoginResponse>> {
    return this.http.post<ApiResponse<LoginResponse>>(`${this.base}/auth/login`, body);
  }
  register(body: RegisterRequest): Observable<ApiResponse<LoginResponse>> {
    return this.http.post<ApiResponse<LoginResponse>>(`${this.base}/auth/register`, body);
  }

  // ── STUDENTS ──────────────────────────────────────────────────────────────
  getStudentDashboard(id: number): Observable<ApiResponse<StudentDashboard>> {
    return this.http.get<ApiResponse<StudentDashboard>>(`${this.base}/students/${id}/dashboard`);
  }
  getStudentGrades(id: number): Observable<ApiResponse<Grade[]>> {
    return this.http.get<ApiResponse<Grade[]>>(`${this.base}/students/${id}/grades`);
  }
  getStudentAverage(id: number): Observable<ApiResponse<number>> {
    return this.http.get<ApiResponse<number>>(`${this.base}/students/${id}/average`);
  }
  getStudentsAtRisk(): Observable<ApiResponse<Student[]>> {
    return this.http.get<ApiResponse<Student[]>>(`${this.base}/students/risk`);
  }
  getStudentsBySpecialty(specialtyId: number): Observable<ApiResponse<Student[]>> {
    return this.http.get<ApiResponse<Student[]>>(`${this.base}/students/specialty/${specialtyId}`);
  }
  updateRiskScore(studentId: number): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>(`${this.base}/students/${studentId}/update-risk`, {});
  }

  // ── PROFESSORS ────────────────────────────────────────────────────────────
  getProfessorDashboard(id: number): Observable<ApiResponse<ProfessorDashboard>> {
    return this.http.get<ApiResponse<ProfessorDashboard>>(`${this.base}/professors/${id}/dashboard`);
  }
  getProfessorStudents(id: number): Observable<ApiResponse<Student[]>> {
    return this.http.get<ApiResponse<Student[]>>(`${this.base}/professors/${id}/students`);
  }
  getPendingResources(professorId: number): Observable<ApiResponse<Resource[]>> {
    return this.http.get<ApiResponse<Resource[]>>(`${this.base}/professors/${professorId}/resources/pending`);
  }
  publishGrade(professorId: number, body: GradeDTO): Observable<ApiResponse<Grade>> {
    return this.http.post<ApiResponse<Grade>>(`${this.base}/professors/${professorId}/grades`, body);
  }
  approveResource(resourceId: number, professorId: number): Observable<ApiResponse<Resource>> {
    return this.http.post<ApiResponse<Resource>>(
      `${this.base}/professors/resources/${resourceId}/approve`, {},
      { params: new HttpParams().set('professorId', professorId) }
    );
  }
  rejectResource(resourceId: number, professorId: number): Observable<ApiResponse<Resource>> {
    return this.http.post<ApiResponse<Resource>>(
      `${this.base}/professors/resources/${resourceId}/reject`, {},
      { params: new HttpParams().set('professorId', professorId) }
    );
  }

  // ── GRADES ────────────────────────────────────────────────────────────────
  // (via professor & student endpoints above)

  // ── EVENTS ────────────────────────────────────────────────────────────────
  getAllEvents(): Observable<ApiResponse<Event[]>> {
    return this.http.get<ApiResponse<Event[]>>(`${this.base}/events`);
  }
  getUpcomingEvents(): Observable<ApiResponse<Event[]>> {
    return this.http.get<ApiResponse<Event[]>>(`${this.base}/events/upcoming`);
  }
  getEventById(id: number): Observable<ApiResponse<Event>> {
    return this.http.get<ApiResponse<Event>>(`${this.base}/events/${id}`);
  }
  createEvent(body: EventDTO, userId: number): Observable<ApiResponse<Event>> {
    return this.http.post<ApiResponse<Event>>(
      `${this.base}/events/create`, body,
      { params: new HttpParams().set('userId', userId) }
    );
  }
  updateEvent(id: number, body: Partial<EventDTO>): Observable<ApiResponse<Event>> {
    return this.http.put<ApiResponse<Event>>(`${this.base}/events/${id}`, body);
  }
  deleteEvent(id: number): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.base}/events/${id}`);
  }
  getEventsByType(type: string): Observable<ApiResponse<Event[]>> {
    return this.http.get<ApiResponse<Event[]>>(`${this.base}/events/type/${type}`);
  }

  // ── RESOURCES ─────────────────────────────────────────────────────────────
  getAllResources(): Observable<ApiResponse<Resource[]>> {
    return this.http.get<ApiResponse<Resource[]>>(`${this.base}/resources`);
  }
  getResourceById(id: number): Observable<ApiResponse<Resource>> {
    return this.http.get<ApiResponse<Resource>>(`${this.base}/resources/${id}`);
  }
  uploadResource(body: ResourceDTO, userId: number): Observable<ApiResponse<Resource>> {
    return this.http.post<ApiResponse<Resource>>(
      `${this.base}/resources/upload`, body,
      { params: new HttpParams().set('userId', userId) }
    );
  }
  getResourcesByType(type: string): Observable<ApiResponse<Resource[]>> {
    return this.http.get<ApiResponse<Resource[]>>(`${this.base}/resources/type/${type}`);
  }
  getResourcesBySubject(subjectId: number): Observable<ApiResponse<Resource[]>> {
    return this.http.get<ApiResponse<Resource[]>>(`${this.base}/resources/subject/${subjectId}`);
  }
  incrementDownload(resourceId: number): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>(`${this.base}/resources/${resourceId}/download`, {});
  }

  // ── SUBJECTS & SPECIALTIES ────────────────────────────────────────────────
  getAllSubjects(): Observable<ApiResponse<Subject[]>> {
    return this.http.get<ApiResponse<Subject[]>>(`${this.base}/subjects`);
  }
  getSubjectsBySpecialty(specialtyId: number): Observable<ApiResponse<Subject[]>> {
    return this.http.get<ApiResponse<Subject[]>>(`${this.base}/subjects/specialty/${specialtyId}`);
  }
  getAllSpecialties(): Observable<ApiResponse<Specialty[]>> {
    return this.http.get<ApiResponse<Specialty[]>>(`${this.base}/specialties`);
  }
}
