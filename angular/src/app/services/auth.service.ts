import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { LoginResponse } from '../models/models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private key = 'enic_user';

  constructor(private router: Router) {}

  setUser(user: LoginResponse) {
    sessionStorage.setItem(this.key, JSON.stringify(user));
  }

  getUser(): LoginResponse | null {
    const s = sessionStorage.getItem(this.key);
    return s ? JSON.parse(s) : null;
  }

  isLoggedIn(): boolean { return !!this.getUser(); }

  isStudent(): boolean { return this.getUser()?.role === 'STUDENT'; }
  isProfessor(): boolean {
    const r = this.getUser()?.role;
    return r === 'PROFESSOR' || r === 'CHAIR';
  }

  logout() {
    sessionStorage.removeItem(this.key);
    this.router.navigate(['/login']);
  }
}
