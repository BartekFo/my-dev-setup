---
name: closed-loop-notes
description: >
  Zapisuj notatki ze spotkań tak, by "domykały pętlę" (closed-loop
  conversations). Użyj, gdy tworzysz notatkę ze spotkania, podsumowanie,
  action pointy lub wiadomość na Slacka z ustaleniami. Wymusza, aby każdy
  punkt akcji miał: articulated outcome, assigned owner i agreed deadline.
---

# Closed-loop notes

Metoda dokumentowania ustaleń ze spotkań między Clients / Growth / Delivery,
która ma **sygnalizować i udowadniać rzetelność** (jeden z 4 filarów trust
equation). Źródło: prezentacja "Closed-loop conversations".

## Dlaczego domykamy pętlę na piśmie
- **"Everyone hears what they want to hear"** — mózg źle radzi sobie z
  założeniami/biasami w rozmowie ustnej.
- **"Hot potato!"** — instynkt obrony utrudnia wzięcie pełnej odpowiedzialności.
- **"Less meetings, more impact!"** — bez tego spotkania to kawalkada rozmów
  bez progresu.

## Trzy elementy każdego zamkniętego punktu (OBOWIĄZKOWE)
Każdy action point / ustalenie do dowiezienia MUSI mieć wszystkie trzy:

1. **Articulated outcome** — konkretny rezultat powiązany z priorytetami, z
   jasną definicją sukcesu. Nie "zajmę się X", tylko co dokładnie ma powstać i
   po czym poznamy, że jest zrobione.
2. **Assigned owner** — jedna osoba, której zadajemy pytania o ten punkt (ma
   buy-in, mierzy progres, flaguje ryzyka wcześnie).
3. **Agreed deadline** — konkretna data. Jeśli na spotkaniu nie ustalono daty,
   NIE zmyślaj jej — oznacz `⏳ TBD` i wypisz jako rzecz do domknięcia.

Przykład zamkniętego punktu:
> "Deployed screen dla funkcjonalności X (nie design), który przejdzie UAT z
> Jane — owner: Mark — deadline: 4 grudnia (final demo po wstępnym UAT)."

## Kiedy domykać pętlę
Zawsze — to dobra praktyka każdego efektywnego spotkania. Szczególnie ważne dla
tematów high-stakes: zamykanie deala, handover, kick-off, feedback, demo,
planning, retro oraz wszędzie tam, gdzie budujemy zaufanie (wczesne interakcje,
trudne momenty).

## Z kim domykać pętlę
Ze wszystkimi istotnymi stakeholderami: Client, Growth, Team, Leadership.
Zawsze zaproś ich do **pushbacku** — odpowiedź "to nie to, na co liczyliśmy"
oznacza, że system działa (lepiej wyłapać rozjazd teraz niż za 2 miesiące).

## Jak formatować notatkę

### Struktura
1. Nagłówek: temat + data + uczestnicy.
2. (opcjonalnie) Link do tablicy / materiałów (placeholder `<WKLEJ_LINK_TU>`).
3. **Po co się spotkaliśmy** — 1-3 zdania kontekstu.
4. **Co ustaliliśmy** — decyzje (bullet points).
5. **Otwarte (do domknięcia)** — kwestie nierozstrzygnięte, w tym action pointy
   bez ustalonego deadline'u.
6. **Action pointy** — każdy w formacie `Outcome — Owner — Deadline`.
7. Zdanie zamykające zapraszające do pushbacku.

### Wariant Slack
Formatowanie Slacka: `*pogrubienie*`, `_kursywa_`, punktory `•`, bez nagłówków
markdown (`#`). Zwięźle i skanowalnie.

### Wariant log.md (TNN master-log w tym folderze)
Jeśli notatka trafia do `log.md`, użyj formatu master-loga: wpis na górze,
`## <data> · <tytuł>` → `### <Temat>` → `**Decision:**` / `**[ ] Task:**` /
`**Open:**` → `_source:_`. Action pointy (`**[ ] Task:**`) też powinny nieść
outcome + owner + deadline (albo `TBD`).

## Checklista przed wysłaniem
- [ ] Każdy action point ma outcome, ownera i deadline (lub jawne `TBD`).
- [ ] Outcome jest konkretny i ma definicję sukcesu (nie "zajmę się").
- [ ] Owner to jedna osoba, nie zespół "wszyscy".
- [ ] Decyzje są oddzielone od kwestii otwartych.
- [ ] Jest zaproszenie do pushbacku stakeholderów.
