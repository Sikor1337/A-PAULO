# PAP-78: moduł audytowy

## Cel i granice

Moduł `app.modules.audit` jest niezależnym, append-only magazynem historii zmian.
Nie zna reguł uprawnień modułów biznesowych i nie wystawia własnego publicznego API.
Endpoint historii należy do modułu będącego właścicielem danych, np.
`GET /beneficiaries/{id}/audit`, ponieważ to on sprawdza dostęp użytkownika.

Kod biznesowy zależy wyłącznie od `AuditPort` i `AuditReaderPort` z
`app.core.audit`. Implementację `SqlAuditService` przekazuje FastAPI Dependency
Injection. Bezpośredni import `app.modules.audit` w serwisie biznesowym jest
niedozwolony.

## Transakcja

`SqlAuditService.record()` dodaje wpis do tej samej sesji SQLAlchemy co zmiana
biznesowa, lecz nie wykonuje `commit()`. Jeden commit serwisu biznesowego zapisuje
obie operacje. Rollback usuwa obie.

`AuditAwareSession` blokuje commit bez wcześniejszego `audit.record()`. Operacje,
które nie zostały jeszcze objęte audytem, muszą jawnie użyć
`repository.commit(skip_audit=True)`. Jest to stan przejściowy i czytelna lista
miejsc do późniejszej integracji.

```python
delta = calculate_delta(old_state, new_state)
audit.record(
    AuditEntry(
        entity_type=EntityType.PI_BENEFICIARY.value,
        entity_id=str(beneficiary.id),
        action="UPDATE",
        actor_id=str(current_user.id),
        actor_display_name=current_user.email,
        changes=delta,
    )
)
repository.commit()
```

## Trwałość i odczyt

Tabela PostgreSQL `audit_events`:

- przechowuje tylko deltę w JSONB,
- jest partycjonowana po `created_at` i ma partycję domyślną,
- ma indeksy po encji, kontekście, aktorze oraz GIN po zmianach,
- blokuje `UPDATE` i `DELETE` triggerem bazy oraz zdarzeniami ORM,
- odbiera `UPDATE` i `DELETE` roli `fastapi_db_user`, jeśli taka rola istnieje.

Przed utworzeniem partycji okresowej należy przenieść rekordy z partycji
domyślnej dla danego zakresu, a następnie dołączyć nową partycję. Polityka
retencji i harmonogram tworzenia partycji są decyzją operacyjną, nie logiką
modułu.
