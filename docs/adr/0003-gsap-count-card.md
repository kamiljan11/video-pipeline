# ADR-0003 — GSAP jako zależność renderera kart (pilot: karta `count`)

(Numeracja ADR pipeline'u jest osobna od panelu. Pełna analiza pięciu opcji z wagami i źródłami licencji: `panel/docs/adr/0005-animation-library.md`.)

Data: 2026-10-22 | Status: przyjęte, pilot zbudowany | Drzwi: dwukierunkowe | Przegląd: 2026-12-01

**Kontekst:** karty to HTML+CSS renderowany klatka po klatce w Chrome (`gfx/render.mjs`). Same wjazdy CSS nie dają liczników „0 → 95%”, animowanej typografii ani wykresów rysowanych w czasie. Kamil (2026-10-22) zgodził się na pilot („zdecyduj autonomicznie”).

**Decyzja:** dodajemy `gsap@3.15.0` jako jedną zależność npm z przypiętą wersją. Ładujemy go tylko na stronę karty `count`. Oś czasu jest zatrzymana, a na każdej klatce robimy `seek(t)`. Liczby z `text` liczy i formatuje (po polsku) `gfx/count_lib.mjs`.

**Odrzucone alternatywy:**
- **Licznik w czystym JS/CSS bez biblioteki** (np. `requestAnimationFrame` albo `@property` z `counter()`): zero zależności. Każdy następny efekt (tekst litera po literze, morfing SVG, wykresy) wymagałby jednak własnego silnika easingów i osi czasu, czyli kodu, którego nikt nie utrzymuje. GSAP daje to w gotowej formie, a koszt to jedna paczka.
- **Remotion:** przepisanie kart na React i własny renderer, licencja płatna powyżej 3 osób.
- **OpenChatCut:** AGPL i inny model pracy (timeline zamiast planu).
- **Lottie:** gotowe animacje, ale nie tekst z planu. Zostaje jako drugi krok, na ikony.

**Konsekwencje (koszt):**
- Nowa zależność od Webflow (licencja „no charge”; wyłączenie dotyczy tylko narzędzi konkurujących z Webflow). Zmiana licencji = przypięta wersja działa dalej, a rollback to usunięcie typu `count` i paczki.
- +~70 KB JS na stronie karty `count`. Inne typy kart go nie ładują, więc ich `.mov` się nie zmieniają.
- Determinizm jest testowany (`gfx/test/count.test.mjs`: dwa rendery = identyczne klatki). `fmtNum` trafia do strony jako kod źródłowy, więc musi zostać samowystarczalny (komentarz w `count_lib.mjs`).
- Bezpieczeństwo: `npm | GreenSock/Webflow | podpis rejestru + atestacja | brak skryptów install | JS tylko w piaskownicy Chrome karty`.
