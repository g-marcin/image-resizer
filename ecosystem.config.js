const path = require('path');
const isWindows = process.platform === 'win32';
const venvPython = isWindows 
  ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
  : path.join(__dirname, 'venv', 'bin', 'python');

module.exports = {
  apps: [{
    name: 'image-resizer',
    script: venvPython,
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8001',
    interpreter: 'none',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    cwd: __dirname,
    env: {
      NODE_ENV: 'production'
    }
  }]
};

