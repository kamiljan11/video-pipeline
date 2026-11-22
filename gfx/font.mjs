// The card font, shipped with the repo: fonts/Montserrat-VF.ttf = google/fonts ofl/montserrat/Montserrat[wght].ttf
// (SIL Open Font License 1.1, fonts/OFL.txt). One path for every page that is not opened from gfx/ itself.
import path from 'path'; import { fileURLToPath, pathToFileURL } from 'url';

export const FONT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'fonts', 'Montserrat-VF.ttf');
export const FONT_URL = pathToFileURL(FONT).href;
