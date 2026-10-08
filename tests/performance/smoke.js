import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '20s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const baseUrl = __ENV.BASE_URL || 'http://host.docker.internal:8080';

function messageId() {
  const date = new Date().toISOString().slice(0, 10).replaceAll('-', '');
  const suffix = `${__VU}${__ITER}${Math.random().toString(36).slice(2, 7)}`
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 12);
  return `MSG-${date}-${suffix.padEnd(4, '0')}`;
}

export default function () {
  const payload = JSON.stringify({
    message_id: messageId(),
    schema_version: '1.0',
    source_system: 'K6_CLIENT',
    target_system: 'PARTNER_B',
    priority: 'NORMAL',
    data_sensitivity: 'PUBLIC',
    payload_format: 'JSON',
    payload: { event: 'load-smoke', sequence: __ITER },
  });

  const response = http.post(`${baseUrl}/api/v1/transmissions`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'accepted with 202': (result) => result.status === 202,
    'correlation header returned': (result) => Boolean(result.headers['X-Correlation-Id']),
  });
  sleep(0.2);
}
