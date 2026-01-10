# Specyfikacja Wymagań Funkcjonalnych 


# Spis Treści

1. [MVP](#1-mvp)
    - [1.1 Moduł Uwierzytelniania i Profil (Auth)](#11-moduł-uwierzytelniania-i-profil-auth)
    - [1.2 Baza Podopiecznych (Beneficiaries)](#12-baza-podopiecznych-beneficiaries)
    - [1.3 Baza Wolontariuszy](#13-baza-wolontariuszy)
    - [1.4. Pomoc Indywidualna](#14-pomoc-indywidualna)
        - [Wymagania UX interfejsu](#wymagania-ux-interfejsu)
2. [v1.0.0](#2-v100)
    - [2.1 Definicja Ról Systemowych](#21-definicja-ról-systemowych)
        - [2.1.1. Administrator (Superuser)](#211-administrator-superuser)
        - [2.1.2. Koordynator Działu](#212-koordynator-działu-np-koo-pomocy-indywidualnej)
        - [2.1.3. Przewodnik](#213-przewodnik)
        - [2.1.4. Lider Zespołu](#214-lider-zespołu-szef-grupy-u-podopiecznego)
        - [2.1.5. Wolontariusz](#215-wolontariusz)
    - [2.2 Moduł Kart Ewidencyjnych (BO)](#22-moduł-kart-ewidencyjnych-bo)
        - [Obieg Kart BO (Evidence Cards)](#obieg-kart-bo-evidence-cards)
3. [v2.0.0](#3-v200)


---

# 1. MVP

## 1.1 Moduł Uwierzytelniania i Profil (Auth)
*   **Logowanie:** Użytkownik loguje się do systemu za pomocą adresu e-mail i hasła.
*   **Edycja Profilu:** Użytkownik może samodzielnie zmienić swoje dane.

## 1.2 Baza Podopiecznych (Beneficiaries)
*   **Karta Podopiecznego:** System przechowuje następujące dane:
    *   Imię i Nazwisko
    *   Adres zamieszkania (z możliwością podlinkowania do mapy)
    *   Numer telefonu
    *   Opis potrzeb / Notatki itp.
*   **Status BO:** Każdy Podopieczny posiada znacznik logiczny (`Tak/Nie`) określający, czy jest objęty programem Kart Ewidencyjnych.
*   **Widok Tabelaryczny (Excel-like):**
    *   **Prezentacja:** Lista podopiecznych w formie tabeli.
    *   **Filtrowanie i Segregowanie:** Możliwość filtrowania po Nazwisku, Adresie, Statusie BO oraz **Grupie**. Możliwość sortowania kolumn.
    *   **Szybka Edycja:** Możliwość edycji danych (np. zmiana adresu, notatki) bezpośrednio z poziomu widoku listy, bez konieczności wchodzenia w szczegóły rekordu.

## 1.3 Baza Wolontariuszy
*   **Lista Wolontariuszy:** System przechowuje listę z danymi kontaktowymi (Telefon, Email).
*   **Dane dodatkowe:** Prywatne notatki/uwagi (np. dyspozycyjność, status studenta).
*   **Widok Tabelaryczny (Excel-like):**
    *   **Filtrowanie:** Wyszukiwanie po nazwisku, filtrowanie po przypisanych grupach/podopiecznych.
    *   **Szybka Edycja:** Możliwość szybkiej zmiany danych wolontariusza (np. dopisanie uwagi, poprawa telefonu) bezpośrednio w tabeli.

## 1.4. Pomoc Indywidualna 
System musi odwzorować logikę przydzielania wolontariuszy do podopiecznych.

*   **Struktura Grup:**
    *   Podopieczni są podzieleni na **Grupy**.
    *   Każda Grupa posiada wyznaczonego **Lidera Wolontariuszy** (osoba odpowiedzialna za wolontariuszy w tej grupie).
*   **Widok Zarządzania Grupami:**
    *   Tabela wyświetlająca wszystkie Grupy.
    *   Kolumny: Nazwa Grupy, Lider Grupy, Liczba Podopiecznych, Liczba Wolontariuszy.
    *   **Edycja:** Możliwość zmiany nazwy grupy oraz przypisania/zmiany Lidera bezpośrednio w tym widoku.
*   **Przypisania (Assignments):**
    *   Wolontariusze chodzą do konkretnych Podopiecznych w ramach Grup.
    *   Relacja wiele-do-wielu: Jeden podopieczny może mieć wielu wolontariuszy, jeden wolontariusz może odwiedzać kilku podopiecznych (również w różnych grupach).
*   **Filtrowanie kontekstowe:**
    *   Klikając w Grupę, można wyświetlić listę wszystkich należących do niej Podopiecznych oraz działających w niej Wolontariuszy.

### Wymagania UX interfejsu
Kluczowym aspektem MVP jest **efektywność zarządzania danymi**.
*   Unikamy zbędnego "przeklikiwania" się przez podstrony.
*   Tam gdzie to możliwe, stosujemy edycję "in-place" (klikasz w tabelę -> edytujesz -> zapisuje się), aby odwzorować szybkość pracy w Excelu.



# 2. v1.0.0 

## 2.1 Definicja Ról Systemowych

System musi rozróżniać i wymuszać następujące poziomy dostępu. Hierarchia jest liniowa: wyższa rola dziedziczy podstawowe widoki niższej, ale posiada szerszy zakres danych.

### 2.1.1. Administrator (Superuser)
*   **Zasięg:** Cały system.
*   **Uprawnienia:** Pełny dostęp do bazy danych, zarządzanie użytkownikami, konfiguracja słowników, dostęp do panelu Django Admin.

### 2.1.2. Koordynator Działu (np. Koo Pomocy Indywidualnej)
*   **Zasięg:** Cały dział (wszyscy podopieczni i wszyscy wolontariusze).
*   **Uprawnienia:**
    *   Widzi dane wrażliwe (notatki o wolontariuszach, prywatne opisy).
    *   Może przypisywać Przewodników do grup.

### 2.1.3. Przewodnik
*   **Zasięg:** Tylko przypisana **Grupa Podopiecznych**.
*   **Uprawnienia:**
    *   Widzi dane osobowe Podopiecznych w swojej grupie.
    *   Widzi dane Wolontariuszy, którzy opiekują się "jego" Podopiecznymi.
    *   Zarządza przypisaniami (kto chodzi do kogo w ramach jego grupy).

### 2.1.4. Lider Zespołu (Szef grupy u Podopiecznego)
*   **Zasięg:** Jeden konkretny **Podopieczny** (lub kilku).
*   **Uprawnienia:**
    *   Pełni funkcję "Głównego Wolontariusza" przy Podopiecznym.
    *   Ma wyróżniony status w aplikacji (np. ikona korony/gwiazdki).

### 2.1.5. Wolontariusz
*   **Zasięg:** Tylko **przypisani Podopieczni**.
*   **Uprawnienia:**
    *   Dostęp "Need to know" – widzi tylko to, co niezbędne do wykonania zadania.
    *   Brak dostępu do listy wszystkich podopiecznych/wolontariuszy


## 2.2 Moduł Kart Ewidencyjnych (BO)
System umożliwia cyfrowy obieg papierowych kart pracy (zdjęć).

*   **Warunek dostępności:** Funkcja dodania karty jest aktywna tylko dla Podopiecznych ze statusem `BO = TAK`.
*   **Dodawanie Karty:**
    *   Użytkownik wybiera okres (Miesiąc/Rok).
    *   Użytkownik wykonuje zdjęcie karty (integracja z aparatem telefonu) lub wybiera plik z galerii.
    *   Karta otrzymuje status początkowy "Oczekująca".
*   **Weryfikacja i Proces:**
    *   System wyświetla listę przesłanych, niezatwierdzonych kart.
    *   Możliwość podglądu zdjęcia w powiększeniu.
    *   Możliwość zmiany statusu na **"Zatwierdzona"**.
    *   Możliwość zmiany statusu na **"Odrzucona"** z obowiązkowym wpisaniem powodu (komentarza).

### Obieg Kart BO (Evidence Cards)

| Akcja | Wolontariusz / Lider | Przewodnik | Koordynator (Jasta) |
| :--- | :---: | :---: | :---: |
| **Dodanie zdjęcia (Upload)** | ✅ (Tylko dla swoich) | ❌ | ❌ |
| **Podgląd zdjęcia** | ✅ (Swoje) | ✅ (Swojej grupy) | ✅ (Wszystkie) |
| **Zatwierdzenie karty** | ❌ | ❌ | ✅ |
| **Odrzucenie karty** | ❌ | ❌ | ✅ |
| **Usunięcie (przed akceptacją)** | ✅ | ❌ | ✅ |




# 3. v2.0.0 

* rekrutacja podopiecznych
* rekrutacja z google forms podopiecznych do brak mozliwosci pomocy lub obecni - low priority
* rekrutacja wolontariuszy
* komunikacja - moduły do wysyłania per dział/wolonitariusze
* Listy TODO dla działów, osoba, status, zadanie, termin, notatka - do przypisywania do przewodników, księży
* Kalendarz roczny z rozpisanymi wydarzeniami stałymi, rocznymi oraz nowymi do dodawania  ad-hoc
* Działy
    * Grupa Remontowa
    * Pomoc Indywidualna (must have)  
    * Grupa Porządkowa    
    * Fizjoterapia 
    * Media 
    * Księgowość 
    * Szkolenia 
    * Festyn Seniora    
    * Klub seniora    
    * Muzyczni    
    * Gastronomia 
    * Fundraising
    * Nowi Wolontariusze

