const isWindows = process.platform === 'win32';

module.exports = {
  apps: [{
    name: 'image-resizer',
    script: isWindows ? 'start.bat' : 'start.sh',
    interpreter: isWindows ? 'cmd' : 'bash',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    }
  }]
};

