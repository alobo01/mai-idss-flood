import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const backendDir = path.join(__dirname, '..', 'backend');

const env = {
  ...process.env,
  DB_HOST: process.env.DB_HOST || 'localhost',
  DB_PORT: process.env.DB_PORT || '5433',
};

const child = spawn('npm', ['run', 'dev'], {
  cwd: backendDir,
  stdio: 'inherit',
  env,
  shell: process.platform === 'win32',
});

child.on('close', (code) => {
  process.exit(code ?? 0);
});
