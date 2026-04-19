import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Event, EventDTO } from '../../models/models';

@Component({
  selector: 'app-events',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss']
})
export class EventsComponent implements OnInit {
  events: Event[] = [];
  loading = true;
  showModal = false;
  editMode = false;
  editId: number | null = null;
  toast = '';
  toastType = 'success';
  filterType = '';

  form: EventDTO = {
    title: '', eventType: 'HACKATHON', description: '',
    location: '', startDatetime: '', endDatetime: '', maxParticipants: 50
  };

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() { this.load(); }

  load() {
    this.loading = true;
    this.api.getAllEvents().subscribe({
      next: r => { this.loading = false; if (r.success) this.events = r.data; },
      error: () => { this.loading = false; }
    });
  }

  applyFilter() {
    if (!this.filterType) { this.load(); return; }
    this.api.getEventsByType(this.filterType).subscribe({
      next: r => { if (r.success) this.events = r.data; }
    });
  }

  openCreate() {
    this.editMode = false; this.editId = null;
    this.form = { title: '', eventType: 'HACKATHON', description: '', location: '', startDatetime: '', endDatetime: '', maxParticipants: 50 };
    this.showModal = true;
  }

  openEdit(e: Event) {
    this.editMode = true; this.editId = e.id;
    this.form = {
      title: e.title, eventType: e.eventType, description: e.description,
      location: e.location, startDatetime: e.startDatetime?.substring(0, 16) || '',
      endDatetime: e.endDatetime?.substring(0, 16) || '', maxParticipants: e.maxParticipants
    };
    this.showModal = true;
  }

  save() {
    const u = this.auth.getUser()!;
    if (this.editMode && this.editId) {
      this.api.updateEvent(this.editId, this.form).subscribe({
        next: r => { if (r.success) { this.showModal = false; this.load(); this.notify('Événement modifié !'); } }
      });
    } else {
      this.api.createEvent(this.form, u.userId).subscribe({
        next: r => { if (r.success) { this.showModal = false; this.load(); this.notify('Événement créé !'); } }
      });
    }
  }

  delete(id: number) {
    if (!confirm('Supprimer cet événement ?')) return;
    this.api.deleteEvent(id).subscribe({
      next: r => { if (r.success) { this.load(); this.notify('Événement supprimé !', 'error'); } }
    });
  }

  notify(msg: string, type = 'success') {
    this.toast = msg; this.toastType = type;
    setTimeout(() => this.toast = '', 3000);
  }

  // ── UI helpers ──────────────────────────────────────────────────────────────

  getCapacityPct(e: Event): number {
    if (!e.maxParticipants) return 0;
    return Math.round((e.currentParticipants / e.maxParticipants) * 100);
  }

  getCapacityDash(e: Event): string {
    const circumference = 2 * Math.PI * 14;
    const filled = circumference * (this.getCapacityPct(e) / 100);
    return `${filled} ${circumference}`;
  }

  getUpcomingCount(): number {
    const now = new Date();
    return this.events.filter(e => new Date(e.startDatetime) > now).length;
  }

  getTotalParticipants(): number {
    return this.events.reduce((sum, e) => sum + (e.maxParticipants || 0), 0);
  }
}