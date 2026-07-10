# A-PAULO — testowanie i mergowanie PR (batch pap-86…pap-91)

## Kolejność mergowania

```
#45 pap-86  (doc)              — wchodzi czysto
#51 pap-93  (testy backend)    — czysto
#53 pap-75  (przewodnik)       — czysto
#46 pap-87  (e-mail)           — MA migrację
#52 pap-91  (działy)           — MA migrację
#50 pap-88  (dialogi)          — ostatni
```

Po **każdym** merge: `git checkout main && git pull`.

## Migracje — ważne

pap-87 i pap-91 mają migracje i **oba wiszą na `pap96`**. Kto wchodzi **drugi**,
daje dwa heady → popraw 1 linię w jego pliku migracji:

- Merge #46 przed #52: przy #46 nic nie ruszasz. Przed mergem #52 zmień w
  `backend/alembic/versions/20260710_000001_pap91_department_membership.py`:
  `down_revision = "pap87_email_verification"`
- (Odwrotna kolejność: to #46 zmienia `down_revision` na `pap91_dept_membership`.)

Po zmergowaniu obu: `cd backend && alembic upgrade head`, sprawdź
`alembic heads` = **jeden head**.

## Jak testować każdy PR

Checkout brancha, backend `uvicorn app.main:app --reload`, frontend `npm run dev`.

### #45 pap-86 (SPIKE)
Tylko `docs/pap-86-email-spike.md`. Przeczytaj rekomendację (Resend). Nic nie odpalasz.

### #51 pap-93 (testy backend)
`cd backend && pytest`. Ma przejść. Nowe testy zapełniają dziury w
tasks/departments/bug_reports/recruitment/audit.

### #53 pap-75 (przewodnik)
Awatar (lewy dół) → **Przewodnik**. Okno z modułami; sekcje zależne od uprawnień.

### #46 pap-87 (rejestracja + weryfikacja e-mail)
1. `cd backend && alembic upgrade head`, `uvicorn app.main:app --reload`
2. `/register` nowym e-mailem
3. link **w oknie uvicorna** (blok `E-MAIL (console backend)`) — dev nie wysyła realnego maila
4. przed kliknięciem linku login → **403 niezweryfikowany**
5. wklej link `/verify-email?token=...` → login działa
6. reset hasła: `/forgot-password` → link z konsoli → `/reset-password?token=...`
7. każdy test = **nowy e-mail** (throttle na użytkownika)

Prawdziwy mail: w `backend/.env` ustaw `EMAIL_PROVIDER=resend`,
`RESEND_API_KEY=...`, `EMAIL_FROM=<zweryfikowana domena>`.

### #52 pap-91 (działy)
Po `alembic upgrade head`:
1. Wejdź w dział → **Dołącz** (twoje konto musi mieć profil wolontariusza z tym samym e-mailem)
2. jako manager: przy oczekującym → **Zatwierdź** (badge OCZEKUJE)
3. **Opuść dział**

Prośby PENDING nie liczą się do `member_count`.

### #50 pap-88 (dialogi)
Usuń cokolwiek (wolontariusza, zadanie, plik) → ładny popup zamiast okna
przeglądarki. Sprawdź też prompt (np. zmiana nazwy załącznika) i alert
(np. błąd pobrania pliku).
