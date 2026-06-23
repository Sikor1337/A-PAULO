# Kontrakt REST API — Standardy i Konwencje

---

## Spis treści

1. [Konwencje URL](#1-konwencje-url)
2. [Format odpowiedzi](#2-format-odpowiedzi)
3. [Format błędów](#3-format-błędów)
4. [Paginacja](#4-paginacja)
5. [Filtrowanie i sortowanie](#5-filtrowanie-i-sortowanie)
6. [Wersjonowanie API](#6-wersjonowanie-api)
7. [Operacje asynchroniczne](#7-operacje-asynchroniczne)


---

# 1. Konwencje URL

## 1.1. Głębokość hierarchii

Maksymalnie **2 poziomy zagłębienia** (`collection/item/collection`):

```
GET /users/42/orders      ✅
GET /users/42/orders/7/items  ❌  — zbyt głęboko, rozważ /order-items?orderId=7
```

## 1.2. Akcje niestandardowe

Gdy operacja nie pasuje do CRUD, użyj sufiksu z dwukropkiem (Google API style) zamiast czasownika w ścieżce:

```
POST /orders/7:cancel         ✅
POST /orders/7/cancel         ❌
POST /cancelOrder             ❌
```

---

# 2. Format odpowiedzi

## 3.1. Pojedynczy zasób — płaska struktura

```json
{
  "id": 42,
  "name": "Jan Kowalski",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-06-01T08:00:00Z"
}
```

## 3.2. Kolekcja — zawsze opakowana w `data`

```json
{
  "data": [
    { "id": 1, "name": "Jan Kowalski" },
    { "id": 2, "name": "Anna Nowak" }
  ],
  "pagination": {
    "total": 150,
    "limit": 25,
    "offset": 0,
    "nextOffset": 25,
    "prevOffset": null
  }
}
```

## 3.3. Konwencje specyficzne dla projektu

| Zasada | Przykład |
|---|---|
| Wartości pieniężne — integer (grosze/najmniejsza jednostka) | `"amount": 9990` = 99.90 PLN |
| Pola nullable — zawsze explicite `null`, nigdy pominięte | `"middleName": null` |

---

# 3. Format błędów

Każda odpowiedź błędna (4xx, 5xx) zwraca ujednolicony obiekt:

## 4.1. Szablon

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with id 42 not found.",
    "details": []
  }
}
```

## 4.2. Błąd walidacji (400/422) z listą naruszeń

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address."
      },
      {
        "field": "age",
        "message": "Must be greater than 0."
      }
    ]
  }
}
```

## 4.3. Kody błędów aplikacyjnych (`error.code`)

Kody w formacie `SCREAMING_SNAKE_CASE`. Każdy moduł może definiować własne — muszą dziedziczyć z poniższych kategorii:

| Kod | HTTP | Opis |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Błąd walidacji pól wejściowych |
| `INVALID_CREDENTIALS` | 401 | Błędne dane logowania |
| `TOKEN_EXPIRED` | 401 | Token wygasł |
| `INSUFFICIENT_PERMISSIONS` | 403 | Brak uprawnień do operacji |
| `RESOURCE_NOT_FOUND` | 404 | Zasób nie istnieje |
| `RESOURCE_ALREADY_EXISTS` | 409 | Konflikt — duplikat zasobu |
| `UNPROCESSABLE_ENTITY` | 422 | Dane poprawne składniowo, błędne semantycznie |
| `RATE_LIMIT_EXCEEDED` | 429 | Przekroczono limit zapytań |
| `INTERNAL_SERVER_ERROR` | 500 | Nieoczekiwany błąd serwera |

---

# 4. Paginacja

## 5.1. Parametry zapytania

| Parametr | Opis | Domyślna wartość | Maksimum |
|---|---|---|---|
| `limit` | Liczba elementów na stronie | `25` | `100` |
| `offset` | Indeks startowy (0-based) | `0` | — |

```
GET /users?limit=25&offset=50
```

## 5.2. Odpowiedź

```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 25,
    "offset": 50,
    "nextOffset": 75,
    "prevOffset": 25
  }
}
```

- `nextOffset` — `null` jeśli to ostatnia strona
- `prevOffset` — `null` jeśli to pierwsza strona

## 5.3. Zasady

- `limit` > `max` → `400 Bad Request`
- Kolekcja pusta → `200 OK` z `"data": []` i `"total": 0`
- `offset` > `total` → `200 OK` z `"data": []`

---

# 5. Filtrowanie i sortowanie

## 6.1. Filtrowanie — query parameters

```
GET /users?status=active
GET /orders?minAmount=100&status=shipped
GET /products?categoryId=5&inStock=true
```

Filtr po wielu wartościach (semantyka OR):

```
GET /users?status=active,pending
```

## 6.2. Wyszukiwanie pełnotekstowe

```
GET /users?q=kowalski
```

## 6.3. Sortowanie

```
GET /users?sort=lastName           # rosnąco (ASC)
GET /users?sort=-createdAt         # malejąco (DESC) — prefiks minus
GET /users?sort=-createdAt,lastName  # wiele pól — priorytety od lewej
```

## 6.4. Projekcja pól (opcjonalnie)

```
GET /users?fields=id,name,email
```

---

# 6. Wersjonowanie API

## 7.1. Strategia: URI versioning

Wersja jako segment URL — najprostsze podejście, cache-friendly:

```
GET /v1/users
GET /v2/users
```

## 7.2. Zasady

- Nowa wersja **tylko** przy breaking change (usunięcie pola, zmiana struktury, zmiana semantyki)
- Dodanie nowego pola **nie** wymaga nowej wersji (backwards compatible)
- Stare wersje utrzymywane przez minimum **6 miesięcy** po wprowadzeniu nowej
- Deprecated endpoints zwracają nagłówki ostrzegawcze:

```http
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

## 7.3. Co stanowi breaking change

| Breaking change (wymaga nowej wersji) | Non-breaking (bez nowej wersji) |
|---|---|
| Usunięcie pola z odpowiedzi | Dodanie nowego opcjonalnego pola |
| Zmiana nazwy pola | Dodanie nowego endpointu |
| Zmiana typu pola | Dodanie nowego opcjonalnego parametru |
| Zmiana semantyki istniejącego pola | Rozszerzenie listy dozwolonych wartości enum |
| Usunięcie endpointu | Zmiana walidacji na mniej restrykcyjną |

---

# 7. Operacje asynchroniczne

Dla operacji trwających dłużej niż ~2 sekundy — wzorzec Async Request-Reply.

## 8.1. Inicjacja operacji

```http
POST /reports/generate
Content-Type: application/json

{ "type": "annual", "year": 2024 }
```

Odpowiedź:

```http
HTTP/1.1 202 Accepted
Location: /jobs/abc-123

{
  "jobId": "abc-123",
  "status": "pending",
  "statusUrl": "/jobs/abc-123"
}
```

## 8.2. Polling statusu

```http
GET /jobs/abc-123
```

```json
{
  "jobId": "abc-123",
  "status": "in_progress",
  "progress": 45,
  "estimatedCompletionAt": "2024-06-22T15:00:00Z"
}
```

## 8.3. Zakończenie — przekierowanie do wyniku

```http
HTTP/1.1 303 See Other
Location: /reports/789

{
  "jobId": "abc-123",
  "status": "completed",
  "resultUrl": "/reports/789"
}
```

## 8.4. Statusy joba

| Status | Opis |
|---|---|
| `pending` | Oczekuje na przetworzenie |
| `in_progress` | W trakcie przetwarzania |
| `completed` | Zakończony sukcesem |
| `failed` | Zakończony błędem |
| `cancelled` | Anulowany przez użytkownika |

Zakończony błędem zwraca obiekt `error` w ciele odpowiedzi zgodnie z sekcją 3.
