import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { StudentDashboard, ProfessorDashboard } from '../../models/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  loading = true;
  studentData: StudentDashboard | null = null;
  profData: ProfessorDashboard | null = null;
  error = '';

  constructor(public auth: AuthService, private api: ApiService) {}

  ngOnInit() {
    const u = this.auth.getUser()!;
    if (this.auth.isStudent() && u.studentId) {
      this.api.getStudentDashboard(u.studentId).subscribe({
        next: r => { this.loading = false; if (r.success) this.studentData = r.data; else this.error = r.message; },
        error: () => { this.loading = false; this.error = 'Impossible de charger le tableau de bord.'; }
      });
    } else if (this.auth.isProfessor() && u.professorId) {
      this.api.getProfessorDashboard(u.professorId).subscribe({
        next: r => { this.loading = false; if (r.success) this.profData = r.data; else this.error = r.message; },
        error: () => { this.loading = false; this.error = 'Impossible de charger le tableau de bord.'; }
      });
    } else {
      this.loading = false;
    }
  }

  gradeColor(v: number) {
    if (v >= 14) return '#10b981';
    if (v >= 10) return '#f59e0b';
    return '#f43f5e';
  }

  riskBadge(level: string) {
    if (level === 'STABLE') return 'badge-stable';
    if (level === 'ATTENTION_REQUIRED') return 'badge-attention';
    return 'badge-risk';
  }
}
