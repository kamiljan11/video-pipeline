// is this module the script node was started with? Both sides through realpath: ~/video-pipeline is a symlink to
// ~/Dane/video-pipeline, and run_v4.sh starts node through the link while import.meta.url holds the real path, so a plain
// path compare was false and the script ended with exit 0 doing nothing (scene_check, thumbs, post_gfx, webshot until 2026-11-08)
import fs from 'fs'; import { fileURLToPath } from 'url';

export const isMain = moduleUrl => {
  if (!process.argv[1]) return false;
  try { return fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(moduleUrl)); } catch { return false; }
};
