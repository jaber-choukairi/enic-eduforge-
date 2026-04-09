/*import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { EventsComponent } from './components/events/events.component';
import { ResourcesComponent } from './components/resources/resources.component';
import { GradesComponent } from './components/grades/grades.component';
import { StudentsComponent } from './components/students/students.component';
import { ProfessorsComponent } from './components/professors/professors.component';
import { LearningPathComponent } from './components/learning-path/learning-path.component';
import { ExamGeneratorComponent } from './components/exam-generator/exam-generator.component';
export const routes: Routes = [
  { path: 'exam-generator', component: ExamGeneratorComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'events', component: EventsComponent, canActivate: [authGuard] },
  { path: 'resources', component: ResourcesComponent, canActivate: [authGuard] },
  { path: 'grades', component: GradesComponent, canActivate: [authGuard] },
  { path: 'students', component: StudentsComponent, canActivate: [authGuard] },
  { path: 'professors', component: ProfessorsComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'dashboard' },
  { path: 'learning-path', component: LearningPathComponent, canActivate: [authGuard] }
];
*/
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { EventsComponent } from './components/events/events.component';
import { ResourcesComponent } from './components/resources/resources.component';
import { GradesComponent } from './components/grades/grades.component';
import { StudentsComponent } from './components/students/students.component';
import { ProfessorsComponent } from './components/professors/professors.component';
import { LearningPathComponent } from './components/learning-path/learning-path.component';
import { ExamGeneratorComponent } from './components/exam-generator/exam-generator.component';
import { CareerSpaceComponent } from './components/career-space/career-space.component';
import { PlanningComponent } from './components/planning/planning.component';
export const routes: Routes = [
  { path: 'planning', component: PlanningComponent, canActivate: [authGuard] },
  { path: 'exam-generator', component: ExamGeneratorComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'events', component: EventsComponent, canActivate: [authGuard] },
  { path: 'resources', component: ResourcesComponent, canActivate: [authGuard] },
  { path: 'grades', component: GradesComponent, canActivate: [authGuard] },
  { path: 'students', component: StudentsComponent, canActivate: [authGuard] },
  { path: 'professors', component: ProfessorsComponent, canActivate: [authGuard] },
  { path: 'learning-path', component: LearningPathComponent, canActivate: [authGuard] },
  { path: 'career-space', component: CareerSpaceComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'dashboard' }
];