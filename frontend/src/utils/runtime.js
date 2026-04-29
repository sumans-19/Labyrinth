export function getBackendHttpBase() {
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const hostname = window.location.hostname || 'localhost';
  return `${protocol}//${hostname}:8000`;
}

export function getBackendWsBase() {
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
