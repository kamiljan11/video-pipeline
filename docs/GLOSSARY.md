# GLOSSARY

| termin | znaczenie |
|---|---|
| spec | `<dir>/linkedin.json`: tekst posta, hashtagi, pierwszy komentarz i media (`carousel`, `video` albo `grafika.png` obok) |
| kod akceptacji | 12 znaków skrótu tego, co wychodzi publicznie (tekst, tytuł/alt text, komentarz, bajty pliku); drukuje go dry run, `--publish` i kolejka go wymagają |
| dry run | `linkedin.py publish <spec>` bez `--publish`: sprawdza token i autora, pokazuje treść i kod, nic nie wysyła |
| rekord | `<dir>/linkedin.published.json`: zakładany przed pierwszym zapisem do LinkedIn; `published` = post jest, `pending`/`unknown` = mógł wyjść |
| SEEN | `~/.local/state/vp-linkedin/seen/`: ten sam tekst posta z innego katalogu = odmowa (bez duplikatów) |
| kolejka | `~/.local/state/vp-linkedin/queue.jsonl`: pozycje (czas Europe/Warsaw, spec, kod akceptacji) dla `run-due` |
| `waiting` / `due` / `done` | czas nie minął / minął, do publikacji / rekord `published` |
| `late` | czas minął o > 3 h (`MAX_LATE_H`): nie publikujemy starych postów hurtem |
| `stuck <stan>` | rekord istnieje, ale nie `published`: publikacja przerwana, sprawdź profil (RUNBOOK) |
| tik | jedno uruchomienie timera (co 15 min): najwyżej jeden post |
