import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface EduForgeMaterial {
  id: string; title: string; status: string;
  chunk_count: number; subject: string; created_at: string;
}
export interface GenerationJobOut {
  id: string; status: 'queued' | 'running' | 'completed' | 'failed';
  exam_id: string; error_message?: string;
}
export interface QuestionConfig {
  question_type: 'multiple_choice' | 'true_false' | 'short_answer' | 'essay' | 'fill_blank';
  count: number;
  difficulty: 'easy' | 'medium' | 'hard';
}
export interface ExamGenerateRequest {
  title: string; topic?: string; description?: string;
  material_ids: string[];
  question_configs: QuestionConfig[];
  time_limit_min?: number;
}

@Injectable({ providedIn: 'root' })
export class EduforgeService {
  private base = 'http://localhost:8000/api/v1';  // direct — CORS handled by EduForge

  constructor(private http: HttpClient) {}

  private headers(): HttpHeaders {
    const token = localStorage.getItem('eduforge_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  login(username: string, password: string): Observable<{ access_token: string }> {
    const body = new FormData();
    body.append('username', username);
    body.append('password', password);
    return this.http.post<{ access_token: string }>(`${this.base}/auth/login`, body);
  }

  register(username: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.base}/auth/register`, { username, email, password, role: 'teacher' });
  }

  uploadMaterial(file: File, title: string, subject: string): Observable<EduForgeMaterial> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('title', title);
    fd.append('subject', subject);
    return this.http.post<EduForgeMaterial>(`${this.base}/materials/upload`, fd,
      { headers: this.headers() });
  }

  getMaterials(): Observable<EduForgeMaterial[]> {
    return this.http.get<EduForgeMaterial[]>(`${this.base}/materials`,
      { headers: this.headers() });
  }

  generateExam(req: ExamGenerateRequest): Observable<GenerationJobOut> {
    return this.http.post<GenerationJobOut>(`${this.base}/exams/generate`, req,
      { headers: this.headers() });
  }

  pollJob(jobId: string): Observable<GenerationJobOut> {
    return this.http.get<GenerationJobOut>(`${this.base}/jobs/${jobId}`,
      { headers: this.headers() });
  }

  exportExamMarkdown(examId: string, studentView = false): Observable<string> {
    return this.http.get(`${this.base}/exams/${examId}/export/markdown?student_view=${studentView}`,
      { headers: this.headers(), responseType: 'text' });
  }

  openInNewWindow(): void {
    window.open('http://localhost:8000/docs', '_blank');
  }
}