import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EduforgeService, EduForgeMaterial, QuestionConfig } from '../../services/eduforge.service';
import { AuthService } from '../../services/auth.service';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

@Component({
  selector: 'app-exam-generator',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './exam-generator.component.html',
  styleUrls: ['./exam-generator.component.scss']
})
export class ExamGeneratorComponent implements OnInit, OnDestroy {
  step: 'upload' | 'configure' | 'generating' | 'done' = 'upload';
  materials: EduForgeMaterial[] = [];
  selectedMaterialIds: string[] = [];
  examTitle = '';
  examTopic = '';
  questionConfigs: QuestionConfig[] = [
    { question_type: 'multiple_choice', count: 5, difficulty: 'medium' }
  ];
  jobId = '';
  examId = '';
  exportMarkdown = '';
  loading = false;
  error = '';
  pollSub?: Subscription;

  constructor(private eduforge: EduforgeService, public auth: AuthService) {}

  ngOnInit() {
    this.autoLogin();
  }

  autoLogin() {
    const user = this.auth.getUser();
    if (!user) return;

    // Convert email to valid username: ahmed.ben@enic.tn → ahmed_ben_enic_tn
    const username = user.email.replace('@', '_').replace(/\./g, '_');
    const password = 'enic-internal-2024';

    this.eduforge.login(username, password).subscribe({
      next: (res) => {
        localStorage.setItem('eduforge_token', res.access_token);
        this.loadMaterials();
      },
      error: () => {
        // First time — register the account then login
        this.eduforge.register(username, user.email, 'enic-internal-2024').subscribe({
          next: () => {
            this.eduforge.login(username, password).subscribe({
              next: (res) => {
                localStorage.setItem('eduforge_token', res.access_token);
                this.loadMaterials();
              },
              error: () => this.error = 'Could not connect to EduForge'
            });
          },
          error: (e) => {
            console.error('Register error:', e);
            this.error = 'Could not connect to EduForge';
          }
        });
      }
    });
  }

  loadMaterials() {
    this.eduforge.getMaterials().subscribe({
      next: (mats) => this.materials = mats,
      error: () => this.error = 'Could not load materials'
    });
  }

  onFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    const file = input.files[0];
    this.loading = true;
    this.eduforge.uploadMaterial(file, file.name.replace(/\.[^.]+$/, ''), '').subscribe({
      next: (mat) => { this.materials.unshift(mat); this.loading = false; },
      error: () => { this.error = 'Upload failed'; this.loading = false; }
    });
  }

  toggleMaterial(id: string) {
    const idx = this.selectedMaterialIds.indexOf(id);
    idx === -1 ? this.selectedMaterialIds.push(id) : this.selectedMaterialIds.splice(idx, 1);
  }

  addQuestionType() {
    this.questionConfigs.push({ question_type: 'short_answer', count: 3, difficulty: 'medium' });
  }

  removeQuestionType(i: number) {
    this.questionConfigs.splice(i, 1);
  }

  generate() {
    if (!this.selectedMaterialIds.length || !this.examTitle) return;
    this.loading = true;
    this.step = 'generating';
    this.eduforge.generateExam({
      title: this.examTitle,
      topic: this.examTopic,
      material_ids: this.selectedMaterialIds,
      question_configs: this.questionConfigs
    }).subscribe({
      next: (job) => {
        this.jobId = job.id;
        this.examId = job.exam_id;
        this.startPolling();
        this.loading = false;
      },
      error: () => { this.error = 'Generation failed'; this.step = 'configure'; this.loading = false; }
    });
  }

  startPolling() {
    this.pollSub = interval(2000).pipe(
      switchMap(() => this.eduforge.pollJob(this.jobId)),
      takeWhile(job => job.status === 'queued' || job.status === 'running', true)
    ).subscribe({
      next: (job) => {
        if (job.status === 'completed') this.loadExport();
        else if (job.status === 'failed') {
          this.error = job.error_message || 'Generation failed';
          this.step = 'configure';
        }
      }
    });
  }

  loadExport() {
    this.eduforge.exportExamMarkdown(this.examId).subscribe({
      next: (md) => { this.exportMarkdown = md; this.step = 'done'; }
    });
  }

  reset() {
    this.step = 'upload';
    this.selectedMaterialIds = [];
    this.examTitle = '';
    this.examTopic = '';
    this.exportMarkdown = '';
    this.error = '';
    this.questionConfigs = [{ question_type: 'multiple_choice', count: 5, difficulty: 'medium' }];
  }

  openFullApp() { this.eduforge.openInNewWindow(); }

  ngOnDestroy() { this.pollSub?.unsubscribe(); }
}