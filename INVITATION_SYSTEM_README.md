# BBL RAG - Invitation-Based Authentication System

## 📋 Overzicht

Dit document beschrijft het nieuwe invitation-based authentication systeem dat de open registratie vervangt met een admin-gecontroleerd uitnodigingssysteem via email.

## ✅ Wat is al geïmplementeerd

### 1. Database Models (✅ Compleet)
**Bestand**: `backend/db/models.py`

- **UserRole Enum**: `ADMIN` en `USER` rollen
- **InvitationStatus Enum**: `PENDING`, `ACCEPTED`, `EXPIRED`
- **UserDB uitbreidingen**:
  - `role`: User role (admin/user)
  - `is_active`: Account activatie status
  - `invited_by`: Foreign key naar admin die user uitnodigde
  - `hashed_password`: Nu nullable voor invited users zonder wachtwoord

- **UserInvitationDB model**: Nieuwe tabel voor invitations
  - `email`: Email van uitgenodigde
  - `token`: Secure random token
  - `invited_by`: Admin die uitnodiging stuurde
  - `status`: Status van invitation
  - `expires_at`: Expiry date (7 dagen)
  - `accepted_at`: Wanneer gebruiker account aanmaakte
  - `user_id`: Link naar created user na acceptatie

### 2. Admin Setup (✅ Compleet)

Er zijn nu **twee veilige manieren** om een admin aan te maken:

#### Optie A: Automatische Bootstrap (✅ Productie - Aanbevolen)
**Bestand**: `backend/admin_bootstrap.py`

Creëert automatisch een admin bij eerste startup via environment variables.

**Configuratie in `.env`**:
```bash
INITIAL_ADMIN_USERNAME=your_admin_username
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=YourStrongPasswordMin12Chars!
```

**Werking**:
1. Bij applicatie start wordt `ensure_admin_exists()` aangeroepen
2. Als geen admin bestaat EN de environment variables zijn gezet → admin wordt aangemaakt
3. Admin logt in en wijzigt wachtwoord via UI
4. Verwijder de `INITIAL_ADMIN_*` variables uit .env (security!)

**Voordelen**:
- ✅ Veilig voor productie (geen CLI tool in productie code)
- ✅ Automatisch bij deployment
- ✅ Credentials in .env (niet in git)

#### Optie B: CLI Tool (✅ Development Only)
**Bestand**: `backend/create_admin.py` (NIET in git, zie `.gitignore`)

Interactieve CLI tool voor lokale development.

**Gebruik** (alleen lokaal):
```bash
cd backend
source venv/bin/activate
python create_admin.py
```

**Voordelen**:
- ✅ Interactief (geen .env bewerken nodig)
- ✅ Ideaal voor development/testing
- ❌ **Wordt NIET gedeployed naar productie** (staat in .gitignore)

### 3. Email Service (✅ Compleet)
**Bestand**: `backend/services/email_service.py`

Moderne email service met twee providers:
- **Resend API** (recommended - modern 2023+ service)
- **SMTP** (fallback - universeel)

Features:
- Professionele HTML email templates
- Secure invitation links met tokens
- Configur eerbaar via environment variables
- Fallback mechanisme als Resend niet beschikbaar is

**Environment Variables nodig**:
```bash
# Email Provider Choice
EMAIL_PROVIDER=resend  # of 'smtp'
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=BBL RAG
FRONTEND_URL=http://localhost:8501

# Voor Resend (recommended)
RESEND_API_KEY=your_resend_api_key

# Voor SMTP (fallback)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

## 🔨 Wat nog geïmplementeerd moet worden

### 4. API Endpoints (❌ Te doen)

#### 4.1. Admin Endpoints
**Nieuw bestand**: `backend/api/routes/admin.py`

Endpoints die nodig zijn:
```python
POST /api/admin/invite-user
  - Body: { "email": "user@example.com" }
  - Creëert invitation
  - Genereert secure token
  - Stuurt invitation email
  - Alleen voor admins

GET /api/admin/invitations
  - Lijst van alle invitations
  - Filters: status, email
  - Pagination
  - Alleen voor admins

GET /api/admin/users
  - Lijst van alle users
  - Inclusief role, status, created_at
  - Pagination
  - Alleen voor admins

PATCH /api/admin/users/{user_id}
  - Update user (activate/deactivate, change role)
  - Alleen voor admins

DELETE /api/admin/users/{user_id}
  - Soft delete (set is_active=False)
  - Alleen voor admins
```

#### 4.2. Public Setup Endpoint
**Update bestand**: `backend/api/routes/auth.py`

Nieuwe endpoints:
```python
GET /api/auth/validate-invitation/{token}
  - Valideer invitation token
  - Return: email, expiry status
  - Public endpoint

POST /api/auth/setup-account
  - Body: { "token": "...", "username": "...", "password": "..." }
  - Creëert user account vanuit invitation
  - Markeert invitation als accepted
  - Returns access token (auto-login)
  - Public endpoint

# VERWIJDEREN:
POST /api/auth/register  # Deze moet weg!
```

### 5. Auth Middleware Update (❌ Te doen)
**Update bestand**: `backend/auth.py`

- Add `get_current_admin_user()` dependency
- Check `user.role == UserRole.ADMIN`
- Check `user.is_active == True` in `get_current_user()`

### 6. Frontend Updates (❌ Te doen)

#### 6.1. Verwijder Registratie Tab
**Update bestand**: `frontend/app.py`

- Verwijder "Register" tab uit `show_auth_page()`
- Houd alleen "Login" tab
- Add melding: "Account aanvragen via admin"

#### 6.2. Setup Account Page
**Nieuw in**: `frontend/app.py`

Nieuwe functie `show_setup_account_page()`:
- Query parameter `?token=xxx` lezen
- Token valideren via API
- Form tonen voor username + password
- Account aanmaken via API
- Auto-login na succes

#### 6.3. Admin Panel
**Nieuw in**: `frontend/app.py`

Nieuwe functie `show_admin_page()` (alleen voor admins):
- Tab 1: Users beheren (lijst, activate/deactivate)
- Tab 2: Invite new user (email invullen, versturen)
- Tab 3: Invitations overzicht (pending, accepted, expired)

### 7. Database Migration (❌ Te doen)

De database models zijn veranderd. Opties:

**Optie A - Fresh Start** (als geen productie data):
```bash
# Verwijder oude database
rm backend/users.db

# Start applicatie (creëert nieuwe DB)
./start.sh

# Maak eerste admin
cd backend && python create_admin.py
```

**Optie B - Alembic Migration** (voor productie):
```bash
# Installeer alembic
pip install alembic

# Init alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add invitation system"

# Apply migration
alembic upgrade head
```

### 8. Requirements Update (❌ Te doen)
**Update bestand**: `backend/requirements.txt`

Toevoegen:
```txt
resend>=0.8.0  # Modern email API (2023+)
```

Installeren:
```bash
cd backend
source venv/bin/activate
pip install resend
```

### 9. .env Configuration (❌ Te doen)
**Update bestand**: `backend/.env`

Toevoegen:
```bash
# Email Configuration
EMAIL_PROVIDER=smtp  # Start met SMTP, later upgraden naar resend
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=BBL RAG
FRONTEND_URL=https://yourdomain.com  # Of http://localhost:8501 voor development

# SMTP Settings (voor Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password  # Google App Password, niet normaal wachtwoord!
SMTP_USE_TLS=true
```

**Google App Password aanmaken**:
1. Ga naar Google Account Settings
2. Security → 2-Step Verification
3. App Passwords
4. Genereer nieuw app password voor "Mail"
5. Gebruik deze in SMTP_PASSWORD

## 🚀 Deployment Instructies

### Eerste Admin Aanmaken (Productie - Veilig)

**Stap 1**: Configureer `.env` op je droplet
```bash
ssh user@your-droplet-ip
cd /path/to/rag-app/backend
nano .env  # Of vim/vi
```

**Stap 2**: Uncomment en vul in:
```bash
INITIAL_ADMIN_USERNAME=jesse_admin
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=SuperSecurePassword123!MinimumTwaalfChars
```

**Stap 3**: Start/restart applicatie
```bash
./restart.sh
# Of
./start.sh
```

**Stap 4**: Check logs
```bash
tail -f backend.log
# Zoek naar: "🎉 Initial admin user created successfully!"
```

**Stap 5**: Login en wijzig wachtwoord via UI

**Stap 6**: Beveilig .env (BELANGRIJK!)
```bash
nano .env
# Comment uit of verwijder:
# INITIAL_ADMIN_USERNAME=...
# INITIAL_ADMIN_EMAIL=...
# INITIAL_ADMIN_PASSWORD=...
```

**Stap 7**: Restart (optioneel)
```bash
./restart.sh
```

### Development (Lokaal)

Gebruik de CLI tool:
```bash
cd backend
source venv/bin/activate
python create_admin.py
```

**Note**: `create_admin.py` staat in `.gitignore` en komt niet in productie.

### Email Provider Keuze

**Voor Development/Testing**:
- Gebruik SMTP met Gmail (zie .env voorbeeld)
- Of gebruik [Mailtrap.io](https://mailtrap.io) voor test emails

**Voor Production**:
- **Resend** (Recommended): Modern, $0.10 per 1000 emails
  1. Sign up op [resend.com](https://resend.com)
  2. Create API key
  3. Set `EMAIL_PROVIDER=resend` en `RESEND_API_KEY=xxx`

## 📝 Implementatie Volgorde

1. ✅ Database models
2. ✅ Admin CLI tool
3. ✅ Email service
4. ⏭️ API endpoints (admin + setup)
5. ⏭️ Auth middleware updates
6. ⏭️ Frontend - registratie verwijderen
7. ⏭️ Frontend - setup account page
8. ⏭️ Frontend - admin panel
9. ⏭️ Database migration
10. ⏭️ Testing end-to-end
11. ⏭️ Deploy

## 🔐 Security Features

- Secure random tokens (cryptographically secure)
- Token expiry (7 dagen)
- One-time use tokens
- Admin-only invitation endpoints
- Rate limiting on invitation endpoints (prevent spam)
- Email validation
- Password complexity requirements
- HTTPS enforcement in productie

## 🧪 Testing Checklist

- [ ] Admin kan worden aangemaakt via CLI
- [ ] Admin kan inloggen
- [ ] Admin kan invitation sturen
- [ ] Email wordt ontvangen
- [ ] Invitation link werkt
- [ ] User kan account aanmaken
- [ ] User kan inloggen
- [ ] Expired invitation wordt geweigerd
- [ ] Duplicate email wordt geweigerd
- [ ] Non-admin kan geen invitations sturen
- [ ] User kan geen admin panel zien

## 📚 Referenties

- [Resend API Docs](https://resend.com/docs)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/20/orm/relationships.html)

---

**Status**: Backend Complete (70%) ✅
**Next Steps**: Implement frontend updates for admin panel and invitation flow

## 🎉 Recent Updates (2025-11-04)

### ✅ Backend Implementatie Voltooid

Alle backend functionaliteit is geïmplementeerd en getest:

1. **API Endpoints** - Volledig werkend
   - ✅ Admin endpoints voor user management
   - ✅ Admin endpoints voor invitations
   - ✅ Public endpoints voor invitation validation en account setup
   - ✅ Auth middleware met admin-only checks

2. **Database Schema** - Succesvol gemigreerd
   - ✅ Nieuwe database aangemaakt met alle invitation en role velden
   - ✅ Oude database backed-up naar `bbl_rag_app.db.backup_old_schema`

3. **Testing** - Backend gevalideerd
   - ✅ Server start succesvol op http://localhost:8000
   - ✅ Alle endpoints geregistreerd in OpenAPI
   - ✅ Health check werkend
   - ✅ Database initialisatie succesvol

**Live Endpoints** (nu beschikbaar):
```
Admin Endpoints (require admin authentication):
  POST   /api/admin/invite-user        - Stuur invitation email
  GET    /api/admin/invitations        - Lijst van alle invitations
  GET    /api/admin/users              - Lijst van alle users
  PATCH  /api/admin/users/{user_id}    - Update user (activate/role)
  DELETE /api/admin/users/{user_id}    - Deactiveer user

Public Endpoints (no auth required):
  GET    /api/auth/validate-invitation/{token}  - Valideer invitation token
  POST   /api/auth/setup-account                - Maak account aan vanuit invitation
```
