import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Student, Specialty } from '../../models/models';

@Component({
  selector: 'app-students',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './students.component.html',
  styleUrls: ['./students.component.scss']
})
export class StudentsComponent implements OnInit {
  students: Student[] = [];
  atRisk: Student[] = [];
  specialties: Specialty[] = [];
  loading = true;
  toast = '';
  toastType = 'success';
  activeTab: 'all' | 'risk' = 'all';
  filterSpecialty = '';

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    this.api.getAllSpecialties().subscribe({ next: r => { if (r.success) this.specialties = r.data; } });
    this.loadAll();
    this.loadAtRisk();
  }

  loadAll() {
    this.loading = true;
    const u = this.auth.getUser()!;
    this.api.getProfessorStudents(u.professorId!).subscribe({
      next: r => { this.loading = false; if (r.success) this.students = r.data; },
      error: () => { this.loading = false; }
    });
  }

  loadAtRisk() {
    this.api.getStudentsAtRisk().subscribe({
      next: r => { if (r.success) this.atRisk = r.data; }
    });
  }

  filterBySpecialty() {
    if (!this.filterSpecialty) { this.loadAll(); return; }
    this.api.getStudentsBySpecialty(+this.filterSpecialty).subscribe({
      next: r => { if (r.success) this.students = r.data; }
    });
  }

  updateRisk(studentId: number) {
    this.api.updateRiskScore(studentId).subscribe({
      next: r => {
        if (r.success) {
          this.notify('Score de risque mis à jour ✅');
          this.loadAll();
          this.loadAtRisk();
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
    setTimeout(() => this.toast = '', 3000);
  }
}
