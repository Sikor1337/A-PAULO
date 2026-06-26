# Frontend Responsive Layout

## Cel

Widoki frontendu powinny być używalne bez poziomego przewijania na telefonach oraz zachować dotychczasowy, gęstszy układ na desktopie.

## Wzorce

- `PageShell` jest wspólną powłoką widoków chronionych. Na desktopie utrzymuje stały panel boczny, a na mobile pokazuje górny pasek z przyciskiem wysuwanego menu.
- `Sidebar` obsługuje teraz stan otwarcia/zamknięcia na mobile. Po przejściu do innej sekcji zamyka drawer.
- `DataTable` renderuje tabelę od breakpointu `md`, a poniżej `md` pokazuje rekordy jako karty z etykietami pól. Nowe kolumny mogą używać `mobileLabel` albo `hideOnMobile`, jeśli nagłówek nie nadaje się do widoku kart.
- Widok `GroupsPage` ma osobne mobilne prezentacje dla przypisań, kart BO i formularza konfiguracji grupy, ponieważ ich desktopowe tabele są zbyt szerokie dla telefonu.

## Zasady dla kolejnych zmian

- Nowe widoki chronione powinny używać `PageShell`.
- Listy CRUD powinny używać `DataTable`, zamiast ręcznie tworzyć tabele.
- Formularze i filtry powinny przechodzić do jednej kolumny na najmniejszych ekranach oraz używać pól/przycisków o wysokości około `40px` lub większej.
- Poziome przewijanie strony (`body`) nie powinno być wymagane do obsługi podstawowych funkcji.
