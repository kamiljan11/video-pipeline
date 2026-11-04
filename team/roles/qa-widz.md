# 11 QA-widz -> `work/qa/findings.<film>.json`

**Misja:** obejrzeć jak widz i jak Kamil, zanim Kamil obejrzy.

**Metoda:** `critic.py --video`, arkusze klatek (co 2 s pierwszej minuty, potem co 10 s), odsłuch fragmentów (muzyka vs głos).

**Lista:** czy rozdział wchodzi na początku części; czy każda scena czytelna (tekst >= 1,5 s na ekranie na 5 słów);
czy coś zasłania twarz; czy napisy shortów nie wchodzą na twarz; czy muzyka nie zagłusza; czy nic nie miga pustą klatką;
czy miniatura czyta się w 1 s w rozmiarze 168x94.

**Wynik:** findings z czasem i klatką; blocker = wraca do roli. Gotowe gdy brak blockerów.
