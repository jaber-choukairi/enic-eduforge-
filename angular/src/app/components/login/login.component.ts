import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Specialty } from '../../models/models';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  tab: 'login' | 'register' = 'login';
  loading = false;
  error = '';
  success = '';
  specialties: Specialty[] = [];

  login = { email: 'ahmed.ben@enic.edu.tn', password: 'demo123' };

  reg = {
    firstName: '', lastName: '', email: '', password: '',
    role: 'STUDENT',
    specialtyId: null as number | null,
    academicLevel: 'L1',
    groupName: '',
    enrollmentYear: new Date().getFullYear(),
    currentSemester: 1,
    department: '',
    officeEmail: ''
  };

  constructor(private api: ApiService, private auth: AuthService, private router: Router) {}

  ngOnInit() {
    this.api.getAllSpecialties().subscribe({
      next: res => { if (res.success) { this.specialties = res.data; if (this.specialties.length) this.reg.specialtyId = this.specialties[0].id; } },
      error: () => {}
    });
  }

  doLogin() {
    if (!this.login.email || !this.login.password) { this.error = 'Veuillez remplir tous les champs.'; return; }
    this.loading = true; this.error = '';
    this.api.login(this.login).subscribe({
      next: res => {
        this.loading = false;
        if (res.success) { this.auth.setUser(res.data); this.router.navigate(['/dashboard']); }
        else this.error = res.message;
      },
      error: () => { this.loading = false; this.error = 'Erreur de connexion. Le serveur est-il démarré ?'; }
    });
  }

  doRegister() {
    if (!this.reg.firstName || !this.reg.lastName || !this.reg.email || !this.reg.password) {
      this.error = 'Veuillez remplir tous les champs obligatoires.'; return;
    }
    if (this.reg.password.length < 6) { this.error = 'Le mot de passe doit contenir au moins 6 caractères.'; return; }
    if (this.reg.role === 'STUDENT' && !this.reg.specialtyId) { this.error = 'Veuillez sélectionner une spécialité.'; return; }
    if ((this.reg.role === 'PROFESSOR' || this.reg.role === 'CHAIR') && !this.reg.department) {
      this.error = 'Veuillez indiquer votre département.'; return;
    }

    this.loading = true; this.error = ''; this.success = '';

    const body: any = {
      firstName: this.reg.firstName,
      lastName: this.reg.lastName,
      email: this.reg.email,
      password: this.reg.password,
      role: this.reg.role
    };

    if (this.reg.role === 'STUDENT') {
      body.specialtyId = Number(this.reg.specialtyId);
      body.academicLevel = this.reg.academicLevel;
      body.groupName = this.reg.groupName || null;
      body.enrollmentYear = Number(this.reg.enrollmentYear);
      body.currentSemester = Number(this.reg.currentSemester);
    } else {
      body.department = this.reg.department;
      body.officeEmail = this.reg.officeEmail || this.reg.email;
    }

    this.api.register(body).subscribe({
      next: res => {
        this.loading = false;
        if (res.success) {
          this.success = 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.';
          this.tab = 'login';
          this.login.email = this.reg.email;
          this.login.password = '';
          // Reset registration form
          this.reg = { firstName: '', lastName: '', email: '', password: '', role: 'STUDENT',
            specialtyId: this.specialties.length ? this.specialties[0].id : null,
            academicLevel: 'L1', groupName: '', enrollmentYear: new Date().getFullYear(),
            currentSemester: 1, department: '', officeEmail: '' };
        } else {
          this.error = res.message;
        }
      },
      error: () => { this.loading = false; this.error = 'Erreur lors de l\'inscription. Veuillez réessayer.'; }
    });
  }
}
