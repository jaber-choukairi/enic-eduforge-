import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Grade, GradeDTO, Subject, Student } from '../../models/models';

@Component({
  selector: 'app-grades',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './grades.component.html',
  styleUrls: ['./grades.component.scss']
})
export class GradesComponent implements OnInit {
  grades: Grade[] = [];
  subjects: Subject[] = [];
  students: Student[] = [];
  loading = true;
  showModal = false;
  toast = '';
  toastType = 'success';
  activeTab: 'CC' | 'EXAM' = 'CC';

  avg = 0; best = 0;

  form: GradeDTO = {
    studentId: 0, subjectId: 1, gradeType: 'CC1',
    gradeValue: 0, comment: '', academicYear: '2024-2025'
  };

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    // Charger les matières filtrées selon le rôle
    this.api.getAllSubjects().subscribe({
      next: r => {
        if (r.success) {
          if (this.auth.isProfessor()) {
            const dept = this.auth.getUser()?.department || '';
            this.subjects = this.filterSubjectsByDept(r.data, dept);
          } else {
            this.subjects = r.data;
          }
        }
      }
    });

    if (this.auth.isProfessor()) {
      const u = this.auth.getUser()!;
      if (u.professorId) {
        this.api.getProfessorStudents(u.professorId).subscribe({
          next: r => {
            this.loading = false;
            if (r.success) {
              this.students = r.data;
              this.loadAllGrades();
            }
          },
          error: () => { this.loading = false; }
        });
      } else { this.loading = false; }
    } else {
      this.loadGrades();
    }
  }

  // Mapping département → codes matières
  filterSubjectsByDept(all: Subject[], department: string): Subject[] {
    const map: Record<string, string[]> = {
      'Intelligence Artificielle': ['ML301', 'NLP301', 'STAT301'],
      'Tech Club ENIC':            ['ALGO301', 'CV301'],
      // Ajouter d'autres départements ici
    };
    const codes = map[department];
    if (!codes) return all;
    return all.filter(s => codes.includes((s as any).code));
  }

  loadGrades() {
    const u = this.auth.getUser()!;
    if (this.auth.isStudent() && u.studentId) {
      this.api.getStudentGrades(u.studentId).subscribe({
        next: r => {
          this.loading = false;
          if (r.success) { this.grades = r.data; this.computeStats(); }
        },
        error: () => { this.loading = false; }
      });
    } else { this.loading = false; }
  }

  loadAllGrades() {
    this.students.forEach(s => {
      this.api.getStudentGrades(s.id).subscribe({
        next: r => { if (r.success) this.grades = [...this.grades, ...r.data]; }
      });
    });
  }

  computeStats() {
    if (!this.grades.length) return;
    const vals = this.grades.map(g => g.gradeValue);
    this.avg  = vals.reduce((s, v) => s + v, 0) / vals.length;
    this.best = Math.max(...vals);
  }

  get gradesByStudent(): { student: Student; cc: Grade[]; exam: Grade[] }[] {
    return this.students.map(s => {
      const sg = this.grades.filter(g => g.student?.id === s.id);
      return {
        student: s,
        cc:   sg.filter(g => g.gradeType !== 'EXAM'),
        exam: sg.filter(g => g.gradeType === 'EXAM')
      };
    });
  }

  getCC(grades: Grade[], type: string): Grade | null {
    return grades.find(g => g.gradeType === type) || null;
  }

  lastComment(grades: Grade[]): string {
    const withComment = grades.filter(g => g.comment);
    return withComment.length ? withComment[withComment.length - 1].comment : '—';
  }

  openEdit(student: Student, subject: Subject, type = 'CC1') {
    this.form = {
      studentId: student.id,
      subjectId: subject.id,
      gradeType: type,
      gradeValue: 0,
      comment: '',
      academicYear: '2024-2025'
    };
    this.showModal = true;
  }

  publish() {
    const u = this.auth.getUser()!;
    this.api.publishGrade(u.professorId!, this.form).subscribe({
      next: r => {
        if (r.success) {
          this.showModal = false;
          this.notify('Note publiée avec succès ✅');
          this.form = { studentId: 0, subjectId: 1, gradeType: 'CC1', gradeValue: 0, comment: '', academicYear: '2024-2025' };
          this.grades = [];
          this.loadAllGrades();
        } else this.notify(r.message, 'error');
      },
      error: () => this.notify('Erreur lors de la publication', 'error')
    });
  }

  gradeColor(v: number) {
    if (v >= 14) return '#10b981';
    if (v >= 10) return '#f59e0b';
    return '#f43f5e';
  }

  indicator(cc: Grade[]): string {
    if (!cc.length) return '—';
    const avg = cc.reduce((s, g) => s + g.gradeValue, 0) / cc.length;
    const trend = cc.length >= 2 ? cc[cc.length - 1].gradeValue - cc[0].gradeValue : 0;
    if (avg >= 14 && trend >= 0) return 'CVP';
    if (avg >= 10) return 'CV';
    return 'Neutre';
  }

  indicatorClass(ind: string) {
    if (ind === 'CVP') return 'ind-cvp';
    if (ind === 'CV')  return 'ind-cv';
    return 'ind-neutre';
  }

  notify(msg: string, type = 'success') {
    this.toast = msg; this.toastType = type;
    setTimeout(() => this.toast = '', 3500);
  }
}