import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

interface Skill {
  name: string;
  current: number;
  required: number;
}

interface ActionItem {
  color: string;
  label: string;
}

interface Stage {
  company: string;
  role: string;
  location: string;
  duration: string;
  type: string;
  match: number;
  tags: string[];
}

interface Mentor {
  name: string;
  role: string;
  company: string;
  initials: string;
  color: string;
  expertise: string[];
  available: boolean;
}

@Component({
  selector: 'app-career-space',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './career-space.component.html',
  styleUrls: ['./career-space.component.scss']
})
export class CareerSpaceComponent implements OnInit {
  activeTab: 'skillgap' | 'stages' | 'mentorat' = 'skillgap';
  specialty = 'IA';
  objective = 'ML Engineer';
  compatibility = 74;
  loading = false;

  skills: Skill[] = [
    { name: 'Python',        current: 90, required: 95 },
    { name: 'ML Classique',  current: 80, required: 90 },
    { name: 'Deep Learning', current: 65, required: 85 },
    { name: 'NLP',           current: 55, required: 80 },
    { name: 'Statistiques',  current: 50, required: 85 },
    { name: 'MLOps',         current: 30, required: 75 },
    { name: 'SQL/Data',      current: 70, required: 80 },
    { name: 'Communication', current: 75, required: 70 },
  ];

  actionPlan: ActionItem[] = [
    { color: '#f43f5e', label: 'Renforcer : Statistiques & Probabilités' },
    { color: '#f59e0b', label: 'Améliorer : NLP & Transformers' },
    { color: '#818cf8', label: 'Continuer : Deep Learning (bon niveau)' },
    { color: '#10b981', label: 'Excellent : Python & Algorithmes' },
  ];

  stages: Stage[] = [
    { company: 'Vermeg',    role: 'ML Engineer Intern',       location: 'Tunis',    duration: '6 mois', type: 'PFE',   match: 92, tags: ['Python', 'TensorFlow', 'MLOps'] },
    { company: 'Telnet',    role: 'Data Science Intern',      location: 'Ariana',   duration: '3 mois', type: 'Stage', match: 85, tags: ['Python', 'NLP', 'SQL'] },
    { company: 'Talan',     role: 'AI Research Intern',       location: 'Tunis',    duration: '6 mois', type: 'PFE',   match: 78, tags: ['Deep Learning', 'PyTorch'] },
    { company: 'Sofrecom',  role: 'Data Analyst Intern',      location: 'La Marsa', duration: '3 mois', type: 'Stage', match: 72, tags: ['SQL', 'Power BI', 'Python'] },
    { company: 'Expensya',  role: 'NLP Engineer Intern',      location: 'Tunis',    duration: '6 mois', type: 'PFE',   match: 88, tags: ['NLP', 'BERT', 'FastAPI'] },
  ];

  mentors: Mentor[] = [
    { name: 'Dr. Sami Bouaziz',   role: 'ML Lead',          company: 'Vermeg',   initials: 'SB', color: '#0ea5e9', expertise: ['TensorFlow', 'MLOps', 'Python'],   available: true  },
    { name: 'Ing. Nour Mejri',    role: 'Data Scientist',   company: 'Orange TN',initials: 'NM', color: '#10b981', expertise: ['NLP', 'SQL', 'Power BI'],          available: true  },
    { name: 'Dr. Amine Trabelsi', role: 'AI Researcher',    company: 'ENIT',     initials: 'AT', color: '#818cf8', expertise: ['Deep Learning', 'PyTorch', 'CV'],  available: false },
    { name: 'Ing. Rima Chaabane', role: 'Senior Dev',       company: 'Talan',    initials: 'RC', color: '#f59e0b', expertise: ['FastAPI', 'Docker', 'MLflow'],     available: true  },
  ];

  constructor(public auth: AuthService) {}

  ngOnInit() {
    const u = this.auth.getUser();
    if (u?.specialty) this.specialty = u.specialty;
  }

  setTab(tab: 'skillgap' | 'stages' | 'mentorat') {
    this.activeTab = tab;
  }

  getBarColor(current: number, required: number): string {
    const ratio = current / required;
    if (ratio >= 1)   return '#10b981';
    if (ratio >= 0.8) return '#f59e0b';
    if (ratio >= 0.6) return '#f59e0b';
    return '#f43f5e';
  }

  getMatchColor(match: number): string {
    if (match >= 85) return '#10b981';
    if (match >= 70) return '#f59e0b';
    return '#f43f5e';
  }
}