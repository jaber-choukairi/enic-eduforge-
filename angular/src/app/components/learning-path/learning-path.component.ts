import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

interface PathStep {
  title: string;
  description: string;
  status: 'completed' | 'in-progress' | 'upcoming';
  score?: number;
  progress?: number;
}

interface LearningPath {
  title: string;
  tag: string;
  steps: PathStep[];
  objective: string;
  objectiveDesc: string;
  compatibility: number;
  resources: { icon: string; title: string; subtitle: string }[];
}

@Component({
  selector: 'app-learning-path',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './learning-path.component.html',
  styleUrls: ['./learning-path.component.scss']
})
export class LearningPathComponent implements OnInit {
  loading = true;
  error = '';
  path: LearningPath | null = null;

  constructor(public auth: AuthService) {}

  ngOnInit() {
    const u = this.auth.getUser()!;
    this.generatePath(
      u.specialty || 'AI',
      'L3',
      u.riskLevel || 'STABLE',
      u.riskScore || 0
    );
  }

  async generatePath(
    specialty: string,
    level: string,
    riskLevel: string,
    riskScore: number
  ) {
    this.loading = true;
    this.error = '';

    try {
      const prompt = `
Tu es un conseiller pédagogique pour l'ENIC (École Nationale d'Ingénieurs de Carthage), Tunisie.
Un étudiant a ces caractéristiques :
- Spécialité : ${specialty}
- Niveau académique : ${level}
- Niveau de risque : ${riskLevel}
- Score de risque : ${riskScore}%

Génère un parcours d'apprentissage personnalisé en JSON UNIQUEMENT, sans markdown, sans backticks.
Format exact :
{
  "title": "Parcours [Spécialité] — [Métier cible]",
  "tag": "IA",
  "objective": "Nom du métier cible",
  "objectiveDesc": "Description courte en 2-3 phrases du métier et du marché tunisien.",
  "compatibility": 68,
  "steps": [
    { "title": "Titre étape", "description": "Compétences séparées par virgule", "status": "completed", "score": 92 },
    { "title": "Titre étape", "description": "Compétences", "status": "in-progress", "progress": 45 },
    { "title": "Titre étape", "description": "Compétences", "status": "upcoming" }
  ],
  "resources": [
    { "icon": "🎓", "title": "Nom ressource", "subtitle": "Type · durée ou format" },
    { "icon": "📘", "title": "Nom ressource", "subtitle": "Description courte" },
    { "icon": "🏆", "title": "Nom ressource", "subtitle": "Description courte" }
  ]
}
Génère exactement 5 steps et 3 resources adaptés à la spécialité ${specialty} niveau ${level}.
`;

      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' // ⚠️ Replace this!
        },
        body: JSON.stringify({
          model: 'llama-3.3-70b-versatile',
          max_tokens: 1000,
          messages: [{ role: 'user', content: prompt }]
        })
      });

      const data = await response.json();

      // ✅ FIXED: correct parsing
      const text = data.choices?.[0]?.message?.content || '';

      if (!text) {
        throw new Error('Empty response from AI');
      }

      // Clean markdown if any
      const clean = text.replace(/```json|```/g, '').trim();

      // Parse JSON safely
      this.path = JSON.parse(clean);

    } catch (e) {
      console.error('AI ERROR:', e);
      this.error = 'Impossible de générer le parcours. Veuillez réessayer.';
    } finally {
      this.loading = false;
    }
  }

  regenerate() {
    const u = this.auth.getUser()!;
    this.generatePath(
      u.specialty || 'AI',
      u.academicLevel || 'L1',
      u.riskLevel || 'STABLE',
      u.riskScore || 0
    );
  }

  statusIcon(status: string): string {
    if (status === 'completed') return '✓';
    if (status === 'in-progress') return '▶';
    return '';
  }
}