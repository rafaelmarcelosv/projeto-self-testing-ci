import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

export const options = { vus: 50, duration: '20s' };
export const transferLatency = new Trend('transfer_latency_ms');
export const transferErrors = new Rate('transfer_errors');
const base = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export function setup() {
  const random = `${Date.now()}-${Math.random()}`;
  const source = http.post(`${base}/accounts`, JSON.stringify({ owner: 'Conta Origem', initial_balance: '1000000.00' }), { headers: { 'Content-Type': 'application/json' } });
  const target = http.post(`${base}/accounts`, JSON.stringify({ owner: 'Conta Destino', initial_balance: '0' }), { headers: { 'Content-Type': 'application/json' } });
  if (source.status !== 201 || target.status !== 201) throw new Error('Falha na preparação das contas');
  return { source: source.json().id, target: target.json().id, random };
}

export default function (data) {
  const response = http.post(`${base}/transfers`, JSON.stringify({ source_id: data.source, target_id: data.target, amount: '0.01' }), { headers: { 'Content-Type': 'application/json', 'Idempotency-Key': `${data.random}-${__VU}-${__ITER}` } });
  transferLatency.add(response.timings.duration);
  transferErrors.add(response.status !== 201);
  check(response, { 'transferência criada': r => r.status === 201 });
  sleep(0.1);
}
