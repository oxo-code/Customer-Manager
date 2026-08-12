import { execSync, spawnSync } from 'node:child_process';

const ports = process.argv.slice(2).map((p) => Number(p)).filter((p) => Number.isInteger(p) && p > 0);

if (ports.length === 0) {
  process.exit(0);
}

function unique(values) {
  return [...new Set(values)];
}

function freePortsOnWindows(portList) {
  const pids = new Set();

  for (const port of portList) {
    const result = spawnSync(
      'powershell',
      [
        '-NoProfile',
        '-Command',
        `Get-NetTCPConnection -LocalPort ${port} -State Listen | Select-Object -ExpandProperty OwningProcess`,
      ],
      { encoding: 'utf8' }
    );

    if (!result.stdout) {
      continue;
    }

    const ids = result.stdout
      .split(/\r?\n/)
      .map((line) => Number(line.trim()))
      .filter((pid) => Number.isInteger(pid) && pid > 0);

    for (const pid of ids) {
      pids.add(pid);
    }
  }

  for (const pid of pids) {
    try {
      execSync(`taskkill /PID ${pid} /F`, { stdio: ['ignore', 'ignore', 'ignore'] });
      console.log(`Stopped process ${pid}`);
    } catch {
      // Ignore failures to avoid blocking dev start.
    }
  }
}

function freePortsOnUnix(portList) {
  for (const port of portList) {
    try {
      execSync(`lsof -ti tcp:${port} | xargs kill -9`, { stdio: ['ignore', 'ignore', 'ignore'] });
      console.log(`Freed port ${port}`);
    } catch {
      // No listeners or lsof unavailable; ignore.
    }
  }
}

const uniquePorts = unique(ports);

if (process.platform === 'win32') {
  freePortsOnWindows(uniquePorts);
} else {
  freePortsOnUnix(uniquePorts);
}
