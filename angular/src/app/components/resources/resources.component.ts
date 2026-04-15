import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Resource, ResourceDTO, Subject } from '../../models/models';

@Component({
  selector: 'app-resources',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './resources.component.html',
  styleUrls: ['./resources.component.scss']
})
export class ResourcesComponent implements OnInit {
  resources: Resource[] = [];
  pending: Resource[] = [];
  subjects: Subject[] = [];
  loading = true;
  showModal = false;
  toast = '';
  toastType = 'success';
  filterType = '';
  activeTab: 'all' | 'pending' = 'all';

  form: ResourceDTO = {
    title: '', resourceType: 'COURS', subjectId: 1,
    fileUrl: '', fileSizeBytes: 0, description: ''
  };

  typeIcon: Record<string, string> = {
    COURS: '📚', TD: '📝', TP: '🔬', EXAM: '📋', OTHER: '📄'
  };

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    this.api.getAllSubjects().subscribe({ next: r => { if (r.success) this.subjects = r.data; } });
    this.loadAll();
    if (this.auth.isProfessor()) this.loadPending();
  }

  loadAll() {
    this.loading = true;
    const obs = this.filterType
      ? this.api.getResourcesByType(this.filterType)
      : this.api.getAllResources();
    obs.subscribe({
      next: r => { this.loading = false; if (r.success) this.resources = r.data; },
      error: () => { this.loading = false; }
    });
  }

  loadPending() {
    const u = this.auth.getUser()!;
    if (u.professorId) {
      this.api.getPendingResources(u.professorId).subscribe({
        next: r => { if (r.success) this.pending = r.data; }
      });
    }
  }

  upload() {
    const u = this.auth.getUser()!;
    this.api.uploadResource(this.form, u.userId).subscribe({
      next: r => {
        if (r.success) {
          this.showModal = false;
          this.loadAll();
          this.notify('Ressource soumise pour validation !');
          this.form = { title: '', resourceType: 'COURS', subjectId: 1, fileUrl: '', fileSizeBytes: 0, description: '' };
        } else this.notify(r.message, 'error');
      },
      error: () => this.notify('Erreur lors de l\'upload', 'error')
    });
  }

  approve(id: number) {
    const u = this.auth.getUser()!;
    this.api.approveResource(id, u.professorId!).subscribe({
      next: r => { if (r.success) { this.loadPending(); this.loadAll(); this.notify('Ressource approuvée ✅'); } }
    });
  }

  reject(id: number) {
    const u = this.auth.getUser()!;
    this.api.rejectResource(id, u.professorId!).subscribe({
      next: r => { if (r.success) { this.loadPending(); this.notify('Ressource rejetée', 'error'); } }
    });
  }

  download(r: Resource) {
    this.api.incrementDownload(r.id).subscribe();
    if (r.fileUrl) window.open(r.fileUrl, '_blank');
  }

  applyFilter() { this.loadAll(); }

  notify(msg: string, type = 'success') {
    this.toast = msg; this.toastType = type;
    setTimeout(() => this.toast = '', 3000);
  }

  statusBadge(status: string) {
    if (status === 'APPROVED') return 'badge-approved';
    if (status === 'PENDING') return 'badge-pending';
    return 'badge-risk';
  }
}
