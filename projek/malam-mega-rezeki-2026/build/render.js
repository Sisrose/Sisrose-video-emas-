// Render video.html frame demi frame -> ffmpeg (H.264 1080x1920, 30fps) + audio suara asal yang diedit.
// Guna: node render.js <out.mp4>            (render penuh)
//       node render.js --stills <dir> t1 t2  (frame contoh)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const DIR = __dirname, FPS = 30;
(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'video.html'));
  const caps = JSON.parse(fs.readFileSync(path.join(DIR, 'captions.json'), 'utf8'));
  await page.evaluate(c => window.__setup(c), caps);
  if (args[0] === '--stills') {
    const out = args[1]; fs.mkdirSync(out, { recursive: true });
    for (const t of args.slice(2)) {
      await page.evaluate(x => window.__render(x), parseFloat(t));
      await page.screenshot({ path: path.join(out, `f_${t}.png`) });
    }
    await browser.close(); return;
  }
  const total = await page.evaluate(() => window.__TOTAL);
  const N = Math.round(total * FPS);
  const outFile = args[0];
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-i', path.join(DIR, 'voice_edit.wav'),
    '-filter_complex', `[1:a]apad=whole_dur=${(N / FPS).toFixed(3)}[a]`, '-map', '0:v', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', (N / FPS).toFixed(3), '-movflags', '+faststart', outFile],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    await page.evaluate(x => window.__render(x), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${N}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('siap', outFile);
})();
