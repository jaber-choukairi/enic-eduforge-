import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Student, Subject, Grade, GradeDTO } from '../../models/models';

@Component({
  selector: 'app-professors',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './professors.component.html',
  styleUrls: ['./professors.component.scss']
})
export class ProfessorsComponent implements OnInit {
  students: Student[] = [];
  subjects: Subject[] = [];
  pendingGrades: Grade[] = [];
  loading = true;
  showGradeModal = false;
  toast = '';
  toastType = 'success';
  activeTab: 'students' | 'grades' | 'risk' = 'students';
  atRisk: Student[] = [];

  form: GradeDTO = {
    studentId: 0, subjectId: 1, gradeType: 'CC1',
    gradeValue: 0, comment: '', academicYear: '2024-2025'
  };

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    const u = this.auth.getUser()!;
    this.api.getAllSubjects().subscribe({ next: r => { if (r.success) this.subjects = r.data; } });
    if (u.professorId) {
      this.api.getProfessorStudents(u.professorId).subscribe({
        next: r => { this.loading = false; if (r.success) this.students = r.data; },
        error: () => { this.loading = false; }
      });
    } else {
      this.loading = false;
    }
    this.api.getStudentsAtRisk().subscribe({
      next: r => { if (r.success) this.atRisk = r.data; }
    });
  }

  publishGrade() {
    const u = this.auth.getUser()!;
    this.api.publishGrade(u.professorId!, this.form).subscribe({
      next: r => {
        if (r.success) {
          this.showGradeModal = false;
          this.notify('Note publiée avec succès ✅');
          this.form = { studentId: 0, subjectId: 1, gradeType: 'CC1', gradeValue: 0, comment: '', academicYear: '2024-2025' };
        } else this.notify(r.message, 'error');
      },
      error: () => this.notify('Erreur lors de la publication', 'error')
    });
  }

  updateRisk(studentId: number) {
    this.api.updateRiskScore(studentId).subscribe({
      next: r => {
        if (r.success) {
          this.notify('Score de risque mis à jour ✅');
          const u = this.auth.getUser()!;
          if (u.professorId) {
            this.api.getProfessorStudents(u.professorId).subscribe({
              next: r2 => { if (r2.success) this.students = r2.data; }
            });
          }
          this.api.getStudentsAtRisk().subscribe({
            next: r2 => { if (r2.success) this.atRisk = r2.data; }
          });
        }
      }
    });
  }

  riskBadge(level: string) {
    if (level === 'STABLE') return 'badge-stable';
    if (level === 'ATTENTION_REQUIRED') return 'badge-attention';
    return 'badge-risk';
  }

  riskColor(score: number) {
    if (score < 30) return '#10b981';
    if (score < 60) return '#f59e0b';
    return '#f43f5e';
  }

  notify(msg: string, type = 'success') {
    this.toast = msg; this.toastType = type;
    setTimeout(() => this.toast = '', 3500);
  }
}
