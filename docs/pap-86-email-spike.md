# PAP-86 [SPIKE] Rejestracja z prawdziwymi mailami — wybór serwisu

Cel: rejestracja ma wysyłać mail z potwierdzeniem konta (a docelowo też reset
hasła — PAP-87). Potrzebny zewnętrzny serwis do wysyłki e-maili transakcyjnych:
darmowy, bezpieczny, prosty w integracji z FastAPI.

## Czy serwisy, których już używamy, to potrafią?

| Serwis | Wysyłka maili? | Wniosek |
|---|---|---|
| **Vercel** | Nie ma własnej wysyłki; w marketplace poleca zewnętrzne (m.in. Resend) | Nie nadaje się samodzielnie |
| **Render** | Brak wbudowanej wysyłki e-mail | Nie nadaje się samodzielnie |
| **Supabase** | Wbudowany SMTP tylko dla Supabase Auth, limit **3 maile/h**, oficjalnie „nie do produkcji"; do produkcji każą podpiąć własny SMTP | Nie nadaje się (nie używamy Supabase Auth, mamy własny JWT) |

Wniosek: potrzebny dedykowany dostawca e-maili transakcyjnych.

## Porównanie dostawców (stan: lipiec 2026)

| Dostawca | Darmowy plan | Ograniczenia | Integracja | Uwagi |
|---|---|---|---|---|
| **Resend** ✅ | 3 000/mies. (100/dzień), bezterminowo | 1 własna domena, logi 30 dni | HTTP API + oficjalne SDK Pythona | Bez brandingu w mailach; najprostsze API; polecane przez Supabase/Vercel |
| **Brevo** | 300/dzień (~9 000/mies.), bezterminowo | Stopka „Sent with Brevo" na darmowym planie (usunięcie: dodatek $9/mies.) | SMTP + HTTP API | Największy darmowy wolumen; limit wspólny z mailami marketingowymi |
| **Mailgun** | 100/dzień | Mały limit, wymagane dane karty | SMTP + API | Bez przewagi nad Resend |
| **Postmark** | 100/**miesiąc** | Za mało nawet na testy | SMTP + API | Świetna dostarczalność, ale limit dyskwalifikuje |
| **SendGrid** | Brak darmowego planu (od 2025 tylko 60-dniowy trial) | — | — | Odpada |
| **Amazon SES** | 3 000/mies. tylko przez 12 miesięcy | Wymaga konta AWS, karty, wyjścia z sandboxa, samodzielnego dbania o reputację | SMTP + API | Za duży narzut operacyjny dla wolontariatu |

## Rekomendacja: **Resend** (plan darmowy)

Dlaczego:
1. **Wystarczający limit** — 100 maili/dzień pokrywa rejestracje i resety haseł
   organizacji wolontariackiej z dużym zapasem (to nie jest newsletter).
2. **Bez brandingu** — maile wyglądają profesjonalnie od pierwszego dnia
   (Brevo dokleja stopkę na darmowym planie).
3. **HTTP API, nie SMTP** — działa wszędzie (PaaS-y potrafią blokować porty
   SMTP), jeden klucz API w `.env`, oficjalne SDK Pythona (`pip install resend`).
4. **Bezpieczeństwo** — klucz API o ograniczonym zakresie (tylko wysyłka),
   weryfikacja domeny przez SPF/DKIM/DMARC, brak przechowywania haseł SMTP.
5. **Ekosystem** — oficjalne integracje z Vercel i Supabase; jeśli kiedyś
   przejdziemy na Supabase Auth, ten sam dostawca zostaje.

Plan awaryjny: **Brevo**, gdy przekroczymy 100 maili/dzień — interfejs wysyłki
będzie za abstrakcją (patrz niżej), więc podmiana to jedna klasa + config.

### Wymagania wdrożeniowe

- Konto Resend + zweryfikowana domena nadawcy (rekordy SPF/DKIM w DNS domeny
  organizacji). Do czasu podpięcia domeny dev używa `onboarding@resend.dev`
  (wysyłka wyłącznie na adres właściciela konta).
- Nowe zmienne w `.env`: `EMAIL_PROVIDER` (`resend` | `console`),
  `RESEND_API_KEY`, `EMAIL_FROM`, `FRONTEND_BASE_URL` (do budowy linków).
- W testach i dev domyślnie provider `console` (log zamiast realnej wysyłki) —
  zero maili i zero sekretów w CI.

## Szkic implementacji dla PAP-87

Warstwa wysyłki jako port w `app/core` (analogicznie do `AuditPort`):

```
app/infrastructure/email/
    port.py        # EmailPort: send(to, subject, html) — abstrakcja
    resend.py      # ResendEmailBackend (HTTP API)
    console.py     # ConsoleEmailBackend (dev/testy: loguje zamiast wysyłać)
```

Przepływ **potwierdzenia rejestracji**:
1. `POST /auth/register` tworzy konto z `is_active=False` (lub flagą
   `email_verified=False`) + rekord tokenu weryfikacyjnego
   (hash tokenu w DB, TTL 24 h, jednorazowy).
2. Mail z linkiem `{FRONTEND_BASE_URL}/verify-email?token=...`.
3. `POST /auth/verify-email` sprawdza hash tokenu, aktywuje konto, kasuje token.
4. `POST /auth/resend-verification` z limitem (np. 1/min) dla niedoręczonych.

Przepływ **resetu hasła**:
1. `POST /auth/password-reset/request` — zawsze `200` (bez ujawniania, czy
   e-mail istnieje), token resetu (hash w DB, TTL 1 h, jednorazowy).
2. Mail z linkiem `{FRONTEND_BASE_URL}/reset-password?token=...`.
3. `POST /auth/password-reset/confirm` — nowe hasło, kasacja tokenu
   i unieważnienie refresh tokenów użytkownika.

Zasady bezpieczeństwa (obowiązkowe w PAP-87):
- w DB trzymamy **hash** tokenu (SHA-256), nigdy surowy token,
- tokeny jednorazowe z TTL; porównanie stałoczasowe,
- odpowiedzi endpointów nie ujawniają istnienia konta,
- rate limiting na wysyłkę (ochrona przed spamem i wyczerpaniem limitu 100/dzień),
- wysyłka po zatwierdzeniu transakcji DB (jak przy załącznikach w bug reports).

## Źródła

- [Resend — pricing](https://resend.com/pricing) · [nowy darmowy plan](https://resend.com/blog/new-free-tier) · [limity kont](https://resend.com/docs/knowledge-base/account-quotas-and-limits)
- [Brevo — limity darmowego planu](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan) · [cennik](https://www.brevo.com/pricing/)
- [Supabase — własny SMTP wymagany do produkcji](https://supabase.com/docs/guides/auth/auth-smtp) · [integracja Resend](https://supabase.com/partners/integrations/resend)
- [SendGrid — koniec darmowego planu (60-dniowy trial)](https://dreamlit.ai/blog/best-sendgrid-alternatives)
- [Porównanie serwisów transakcyjnych 2026 (Mailtrap)](https://mailtrap.io/blog/transactional-email-services/) · [emailtooltester](https://www.emailtooltester.com/en/blog/best-transactional-email-service/)
