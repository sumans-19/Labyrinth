export function getBackendHttpBase() {
  if (import.meta.env.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL.replace(/\/$/, "");
  }
  if (window.location.hostname !== 'localhost') {
    return 'https://labyrinth-4fap.onrender.com';
  }
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const hostname = window.location.hostname || 'localhost';
  return `${protocol}//${hostname}:8000`;
}

export function getBackendWsBase() {
  if (import.meta.env.VITE_BACKEND_URL) {
    let url = import.meta.env.VITE_BACKEND_URL.replace(/\/$/, "");
    if (url.startsWith('https://')) return url.replace('https://', 'wss://');
    if (url.startsWith('http://')) return url.replace('http://', 'ws://');
    return `wss://${url.replace(/^.*:\/\//, '')}`;
  }
  if (window.location.hostname !== 'localhost') {
    return 'wss://labyrinth-4fap.onrender.com';
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname || 'localhost';
  return `${protocol}//${hostname}:8000`;
}

export function getAttackerConsoleUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set('screen', 'attacker');
  url.searchParams.delete('tab');
  return url.toString();
}

export function getDashboardUrl() {
  const url = new URL(window.location.href);
  url.searchParams.delete('screen');
  url.searchParams.set('tab', 'warroom');
  return url.toString();
}
