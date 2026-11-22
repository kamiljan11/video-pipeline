# Wzorzec: shorty opublikowane na kanale Kamila (26.10-05.11.2026)

Kamil 2026-11-15, po obejrzeniu shortów filmu 2: „powinieneś sobie obejrzeć jakość shortów, jaką mieliśmy w pierwszych filmikach,
bo tam jest dużo logik naprawionych i ty o nich chyba zapomniałeś; tam było dużo lepiej rysowanie, te bycie w kółku też".
Na pytanie, o który wzorzec chodzi: „musiałbyś obejrzeć te wszystkie shorty, co wystawiłem, i się nauczyć".

Źródło: 10 publicznych shortów z kanału (tl5EDHjKT4k, 5NWqYpC1bSA, u90flYL5-f0, SCqEvGG1Lq0, dkuR9M1-sBk, drFuW0UgxKI,
E7sEnipSqX0, fJ7eaEfgYYg, 7oYHpooG-bw, huuT5A8hcPk), klatki co 2 s. Kod, który je zrobił:
`~/Dane/Videos/Montaz/2026-10-31_promo95_archiwum/_skrypty_i_backupy/gen_floats2.py` (+ `gen_c3.py`, `gen_c5.py`,
plany `plans_bak_1031b/plan_cetus_c*.json`). Najlepsze (ostatnie): drFuW0UgxKI, E7sEnipSqX0, fJ7eaEfgYYg, huuT5A8hcPk.

## Co tam jest, a czego brakowało w shortach filmu 2 (render 2026-11-15)

| element | opublikowane (wzorzec) | film 2 przed poprawką |
|---|---|---|
| motyw | `cetus` (granat, niebieski akcent `#086AD8`/`#6FA7EC`, biały papier) | brak `work/theme.json` -> domyślny turkus szablonu |
| karta | JASNA: biała kartka w linie (notes) albo okno aplikacji z trzema kropkami, gruba niebieska ramka, duży tekst 35-54 px, na całą szerokość (x 30-1050) | ciemne, małe elementy sceny na czarnym tle, puste miejsce pod nimi |
| rysowanie | jedna kartka ROŚNIE w rytm słów: tytuł, wiersze pisane piórem (`.w` clip-path), znaki zapytania, potem liczby, marker pod wierszem; ta sama kartka wraca w kolejnej karcie z tym, co już było napisane | wiele osobnych scen, element wchodzi i ginie, start z jednym elementem i pustką |
| układ A (split) | jasne tło (gradient `--soft-2` -> `--paper`), karta u góry, napis pod kartą, twarz w szerokim boksie 972 px pod spodem, cała głowa z ramionami | boks 820 px |
| układ B (kółko) | GRANATOWE tło z niebieskimi poświatami (`DARK`), biała karta u góry, kółko w prawym dolnym rogu, twarz WYPEŁNIA kółko (ciasno: głowa), cienka niebieska obwódka, ciepła miękka poświata | czarne tło, mała twarz w kółku (widać pokój), czerwona poświata od koszulki, turkusowa obwódka |
| napisy | w granatowym pasku (`caption_box`), WERSALIKI, słowo kluczowe niebieskie, 2-3 słowa | bez paska, zdania małymi literami, zielone słowo |
| hook | tekst pisany na jasnym, półprzezroczystym pasku na wysokości klatki piersiowej, druga linia niebieska | biały tekst na twarzy |
| belka | „Kamil Jan / Cetus Automation" w lewym górnym rogu na początku | brak |
| dowód | prawdziwy PDF (okno, przewijanie, żółty marker na zdaniu, podpis źródła pod oknem) | karta tekstowa |
| koniec | granatowa plansza „Pełny odcinek / Cały film na kanale", `Subskrybuj @kamiljan11` / `YouTube: @kamiljan11`, Kamil Jan, kamiljan.com | nowa plansza końcowa (zostaje, Kamil 2026-11-15) |
| tło zdjęciowe | stock (zegar, biuro) na pełny ekran z napisem | memy |

## Zasady na kolejne shorty (obowiązują od filmu 2)
1. Shorty w motywie `cetus` (jasny papier na granacie), nie w domyślnym turkusie.
2. Rysunek w shorcie = jedna jasna kartka/okno, która rośnie słowo po słowie; ten sam przykład na tej samej kartce do końca.
3. Kartka zaczyna się od tytułu i pierwszego wiersza, nie od pustki; tekst >= 35 px na 1080.
4. Kółko: twarz ciasno (głowa wypełnia koło), granatowe tło, niebieska obwódka, poświata bez koloru koszulki.
5. Napisy w pasku, wersalikami.
6. Nie wszystko na kartce (Kamil 2026-11-15: „nie wszystko jest na kartce, są różne sposoby"). Forma karty idzie za treścią:
   łańcuch kroków = schemat z pudełkami i strzałkami; okno, terminal, przełącznik, czat = okno aplikacji z trzema kropkami;
   reszta = kartka w linie. Do tego prawdziwe źródło (PDF, strona) i stock na pełny ekran, jak w tabeli wyżej.
