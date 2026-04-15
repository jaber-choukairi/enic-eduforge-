import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Subject } from '../../models/models';

export interface PlanningSlot {
  id: string;
  subjectId: number;
  subjectName: string;
  type: 'COURS' | 'TD' | 'TP' | 'REVISION' | 'EXAM';
  day: number; // 0=Mon … 6=Sun
  hour: number; // 8..18
  duration: number; // in hours
  location?: string;
  color: string;
}

const SLOT_COLORS = [
  '#1a6b4a', // teal-dark
  '#1a3f6b', // blue-dark
  '#5c1a6b', // purple-dark
  '#6b4f1a', // amber-dark
  '#1a5c6b', // cyan-dark
  '#6b1a2f', // rose-dark
];

const TYPE_LABELS: Record<string, string> = {
  COURS: 'Cours',
  TD: 'TD',
  TP: 'TP',
  REVISION: 'Révision',
  EXAM: 'Exam',
};

@Component({
  selector: 'app-planning',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './planning.component.html',
  styleUrls: ['./planning.component.scss'],
})
export class PlanningComponent implements OnInit {
  Math = Math;
  loading = true;
  error = '';

  subjects: Subject[] = [];
  slots: PlanningSlot[] = [];

  // Week navigation
  currentWeekStart: Date = this.getMonday(new Date());
  weekDays: Date[] = [];
  hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18];
  dayLabels = ['LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM', 'DIM'];

  // Add slot modal
  showModal = false;
  editSlot: Partial<PlanningSlot> = {};
  slotTypes: Array<PlanningSlot['type']> = ['COURS', 'TD', 'TP', 'REVISION', 'EXAM'];

  constructor(public auth: AuthService, private api: ApiService) {}

  ngOnInit() {
    this.buildWeekDays();
    this.loadSubjects();
  }

  // ── Data ──────────────────────────────────────────────────────────────────

  loadSubjects() {
    const u = this.auth.getUser();
    if (!u) { this.loading = false; return; }

    // Load subjects: students by specialty, professors by all
    const obs = u.studentId
      ? this.api.getAllSubjects()
      : this.api.getAllSubjects();

    obs.subscribe({
      next: r => {
        this.loading = false;
        if (r.success) {
          this.subjects = r.data;
          this.autoGenerateSchedule();
        } else {
          this.error = r.message;
        }
      },
      error: () => { this.loading = false; this.error = 'Impossible de charger les matières.'; }
    });
  }

  autoGenerateSchedule() {
    // Generate a realistic weekly schedule from available subjects
    const days = [0, 1, 2, 3, 4]; // Mon-Fri
    const typeRotation: PlanningSlot['type'][] = ['COURS', 'TD', 'TP', 'REVISION'];
    let slotHours = [8, 10, 14, 16];
    this.slots = [];

    this.subjects.slice(0, 8).forEach((subj, i) => {
      const color = SLOT_COLORS[i % SLOT_COLORS.length];
      const day = days[i % days.length];
      const hour = slotHours[i % slotHours.length];
      const type = typeRotation[i % typeRotation.length];

      this.slots.push({
        id: `auto-${subj.id}`,
        subjectId: subj.id,
        subjectName: subj.name,
        type,
        day,
        hour,
        duration: type === 'COURS' ? 2 : 1,
        location: type === 'TP' ? 'Labo ' + (i + 1) : type === 'COURS' ? 'Amphi ' + String.fromCharCode(65 + (i % 4)) : 'Salle ' + (10 + i),
        color,
      });
    });
  }

  // ── Week navigation ───────────────────────────────────────────────────────

  getMonday(d: Date): Date {
    const date = new Date(d);
    const day = date.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    date.setDate(date.getDate() + diff);
    date.setHours(0, 0, 0, 0);
    return date;
  }

  buildWeekDays() {
    this.weekDays = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(this.currentWeekStart);
      d.setDate(d.getDate() + i);
      return d;
    });
  }

  prevWeek() { this.currentWeekStart.setDate(this.currentWeekStart.getDate() - 7); this.buildWeekDays(); }
  nextWeek() { this.currentWeekStart.setDate(this.currentWeekStart.getDate() + 7); this.buildWeekDays(); }

  get weekRangeLabel(): string {
    const end = this.weekDays[6];
    const months = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'];
    if (this.currentWeekStart.getMonth() === end.getMonth()) {
      return `Semaine du ${this.currentWeekStart.getDate()}–${end.getDate()} ${months[end.getMonth()]} ${end.getFullYear()}`;
    }
    return `${this.currentWeekStart.getDate()} ${months[this.currentWeekStart.getMonth()]} – ${end.getDate()} ${months[end.getMonth()]} ${end.getFullYear()}`;
  }

  // ── Slot helpers ──────────────────────────────────────────────────────────

  getSlotsForCell(dayIdx: number, hour: number): PlanningSlot[] {
    return this.slots.filter(s => s.day === dayIdx && s.hour === hour);
  }

  slotHeightPx(duration: number): string {
    return `${duration * 58}px`;
  }

  typeLabel(type: string): string {
    return TYPE_LABELS[type] || type;
  }

  subjectColorFor(subjectId: number): string {
    const idx = this.subjects.findIndex(s => s.id === subjectId);
    return SLOT_COLORS[idx % SLOT_COLORS.length];
  }

  // ── Stats ─────────────────────────────────────────────────────────────────

  get totalHoursThisWeek(): number {
    return this.slots.reduce((acc, s) => acc + s.duration, 0);
  }

  get nextExam(): PlanningSlot | null {
    return this.slots.find(s => s.type === 'EXAM') || null;
  }

  get aiSuggestion(): string {
    const atRisk = this.subjects.find(s => s.credits >= 3);
    if (atRisk) return `Renforcer ${atRisk.name} — ${atRisk.credits} crédits à consolider`;
    return 'Votre planning est bien équilibré cette semaine.';
  }

  // ── Modal ─────────────────────────────────────────────────────────────────

  openAddModal(day?: number, hour?: number) {
    this.editSlot = {
      day: day ?? 0,
      hour: hour ?? 8,
      duration: 1,
      type: 'COURS',
      subjectId: this.subjects[0]?.id,
    };
    this.showModal = true;
  }

  closeModal() { this.showModal = false; }

  saveSlot() {
    const subj = this.subjects.find(s => s.id === Number(this.editSlot.subjectId));
    if (!subj || this.editSlot.day === undefined || !this.editSlot.hour) return;

    const idx = this.subjects.indexOf(subj);
    const newSlot: PlanningSlot = {
      id: 'custom-' + Date.now(),
      subjectId: subj.id,
      subjectName: subj.name,
      type: this.editSlot.type!,
      day: Number(this.editSlot.day),
      hour: Number(this.editSlot.hour),
      duration: Number(this.editSlot.duration) || 1,
      location: this.editSlot.location,
      color: SLOT_COLORS[idx % SLOT_COLORS.length],
    };
    this.slots.push(newSlot);
    this.showModal = false;
  }

  removeSlot(id: string) {
    this.slots = this.slots.filter(s => s.id !== id);
  }
}