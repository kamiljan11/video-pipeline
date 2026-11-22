# 7 Scout shortów -> `work/clips.json`

**Misja:** znaleźć WSZYSTKIE dobre shorty, nie stałą liczbę (Kamil 4.11: „nie wiem czy nie jesteś leniwy z ilością shortów”).

**Metoda:** przejdź cały transkrypt; każda samodzielna myśl 30-55 s to kandydat (= producent-shortow, film_check short.length_min/max; krótsza myśl -> dołóż
  sąsiednie zdanie kontekstu albo `make: false`). Oceń każdego, zapisz wszystkich.

**Rubryka (shorts_sound.md Top 15, ZASADY-KAMILA-SHORTY.md), 0-3 pkt za każde:**
1. hook w pierwszych 3 s (pytanie, konflikt, liczba, zaskoczenie)
2. samodzielność: zrozumiały bez longa
3. jedna myśl, puenta na końcu
4. da się pokazać obrazem (scena, web, meme)
5. pętla: koniec łączy się z początkiem
6. wartość dla widza (konkret, nie ogólnik)

`make: true` gdy suma >= 12/18 i hook >= 2. Różne kandydaty nie dublują tej samej puenty.

**Artefakt:**
```json
{"items": [{"id": "s1", "w0": 120, "w1": 210, "title_work": "…", "score": {"hook": 3, "alone": 2, "one": 3, "visual": 2, "loop": 1, "value": 3},
            "total": 14, "make": true, "why": "…",
            "hooks": ["…", "…", "…", "…", "…"], "hook": "…", "hook_from": "mech-contrarian"}]}
```

**Hooki (Skool CCC B05, So2):** na każdy short z `make: true` 5 wariantów w `hooks` (min. 3), każdy z innego mechanizmu
`style/hook_bank.json` (wiersz `own-*` = nasz sprawdzony, `mech-*` = mechanizm do przerobienia: mechanizm zostaje, temat nasz,
słowa nigdy cudze). `hook` = wybrany (trafia do `hook_text` planu), `hook_from` = id wiersza banku. Każdy wariant przechodzi
`python3 hook_check.py "<hook>"`: bez powitania, bez tytułu-listy („5 porad”), bez rozbiegu („Dzisiaj”, „W tym filmie”), bez
mglistej obietnicy i stosu przymiotników, ze stawką (liczba albo słowo straty/zysku), <= 12 słów. Słowniki: `style/hook_lint.json`.

**Przegląd tygodnia (właściciel: Kamil albo rola social, w poniedziałek; ADR-0016):** dla każdego shorta starszego niż 7 dni
z `hook_from` wpisz w jego wierszu `style/hook_bank.json` `result` = wyświetlenia shorta / mediana wyświetleń kanału z 28 dni
(YouTube Studio, liczby ręcznie, nigdy zgadnięte). Hook z `result` >= 1.5 (próg startowy, do zmiany po pierwszym miesiącu danych) dopisz jako nowy wiersz `own-*` z `why`.

**Gotowe gdy:** każdy kandydat z oceną; `make` zgodny z progiem; `film_check --out` out.hooks OK.
