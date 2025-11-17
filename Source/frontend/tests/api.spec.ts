import { test, expect, APIRequestContext } from '@playwright/test';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:18080';
const apiUrl = (path: string) => `${API_BASE_URL}${path}`;

const getJson = async <T>(request: APIRequestContext, path: string, expectedStatus = 200): Promise<T> => {
  const response = await request.get(apiUrl(path));
  expect(response.status(), `GET ${path} should return ${expectedStatus}`).toBe(expectedStatus);
  return response.json();
};

test.describe('Flood Prediction API parity with PLAN', () => {
  test('health + docs endpoints are reachable', async ({ request }) => {
    const health = await getJson<{ status: string }>(request, '/health');
    expect(health.status).toBe('ok');

    const openApiResponse = await request.get(apiUrl('/api/openapi.json'));
    expect(openApiResponse.status()).toBe(200);

    const docsResponse = await request.get(apiUrl('/api-docs'));
    expect(docsResponse.status()).toBe(200);
  });

  test('zones endpoint matches PLAN zone schema (Section 6.1)', async ({ request }) => {
    const geoJson = await getJson<any>(request, '/api/zones');
    expect(geoJson.type).toBe('FeatureCollection');
    expect(Array.isArray(geoJson.features)).toBe(true);
    expect(geoJson.features.length).toBeGreaterThanOrEqual(4);

    const sample = geoJson.features[0];
    expect(sample.properties.id).toMatch(/^Z-/);
    expect(typeof sample.properties.name).toBe('string');
    expect(Array.isArray(sample.properties.critical_assets)).toBe(true);
    expect(sample.properties.population).toBeGreaterThan(0);
  });

  test('assets endpoint exposes critical infrastructure (PLAN §3 Map)', async ({ request }) => {
    const assets = await getJson<Array<{
      id: string;
      zoneId: string;
      type: string;
      criticality: string;
      location: { type: string; coordinates: [number, number] };
    }>>(request, '/api/assets');

    expect(assets.length).toBeGreaterThan(0);
    assets.forEach(asset => {
      expect(asset.id).toBeTruthy();
      expect(asset.zoneId).toMatch(/^Z-/);
      expect(typeof asset.type).toBe('string');
      expect(asset.criticality).toMatch(/low|medium|high|critical/i);
      expect(asset.location?.type).toBe('Point');
      expect(Array.isArray(asset.location?.coordinates)).toBe(true);
    });

    const targetZone = assets[0]?.zoneId;
    if (targetZone) {
      const filtered = await getJson<Array<{ zoneId: string }>>(request, `/api/assets?zoneId=${encodeURIComponent(targetZone)}`);
      expect(filtered.length).toBeGreaterThan(0);
      filtered.forEach(asset => expect(asset.zoneId).toBe(targetZone));
    }
  });

  test('risk endpoint respects time horizon + drivers (PLAN §3 Planner)', async ({ request }) => {
    const risk = await getJson<Array<{
      zoneId: string;
      risk: number;
      drivers: Array<{ feature: string; contribution: number }>;
      thresholdBand: string;
      etaHours: number;
    }>>(request, '/api/risk?at=2025-11-11T12-00-00Z&timeHorizon=12h');

    expect(risk.length).toBeGreaterThan(0);
    for (const entry of risk) {
      expect(entry.zoneId).toMatch(/^Z-/);
      expect(entry.risk).toBeGreaterThanOrEqual(0);
      expect(entry.risk).toBeLessThanOrEqual(1);
      expect(entry.thresholdBand).toMatch(/Low|Moderate|High|Severe/);
      expect(Array.isArray(entry.drivers)).toBe(true);
      expect(entry.drivers.length).toBeGreaterThan(0);
      entry.drivers.forEach(driver => {
        expect(typeof driver.feature).toBe('string');
        expect(driver.contribution).toBeGreaterThanOrEqual(0);
      });
    }
  });

  test('resources endpoint groups depots/equipment/crews (PLAN §3 Coordinator/Admin)', async ({ request }) => {
    const resources = await getJson<{
      depots: Array<{ id: string; name: string; lat: number; lng: number }>;
      equipment: Array<{ id: string; type: string; depot: string; status: string }>;
      crews: Array<{ id: string; skills: string[]; status: string }>;
    }>(request, '/api/resources');

    expect(resources.depots.length).toBeGreaterThan(0);
    resources.depots.forEach(d => {
      expect(d.id).toMatch(/^D-/);
      expect(typeof d.lat).toBe('number');
    });

    expect(resources.equipment.length).toBeGreaterThan(0);
    resources.equipment.forEach(eq => {
      expect(eq.id).toMatch(/^(P|S|V)-/);
      expect(typeof eq.depot).toBe('string');
    });

    expect(resources.crews.length).toBeGreaterThan(0);
    resources.crews.forEach(crew => {
      expect(crew.id).toMatch(/^C-/);
      expect(Array.isArray(crew.skills)).toBe(true);
    });

    const sampleCrew = resources.crews.find(crew => crew.status);
    if (sampleCrew) {
      const filtered = await getJson<{
        depots: unknown[];
        equipment: unknown[];
        crews: Array<{ status: string }>;
      }>(request, `/api/resources?type=crew&status=${encodeURIComponent(sampleCrew.status)}`);

      expect(filtered.depots.length).toBe(0);
      expect(filtered.equipment.length).toBe(0);
      expect(filtered.crews.length).toBeGreaterThan(0);
      filtered.crews.forEach(entry => expect(entry.status).toBe(sampleCrew.status));
    }
  });

  test('alerts can be acknowledged (PLAN §3 Coordinator)', async ({ request }) => {
    const alerts = await getJson<Array<{ id: string; severity: string }>>(request, '/api/alerts');
    expect(alerts.length).toBeGreaterThan(0);

    const target = alerts[0];
    const ackResponse = await request.post(apiUrl(`/api/alerts/${target.id}/ack`), {
      data: { acknowledgedBy: 'Playwright Test' },
    });
    expect(ackResponse.status()).toBe(200);
    const ackBody = await ackResponse.json();
    expect(ackBody.success).toBe(true);
    expect(ackBody.alert.acknowledged).toBe(true);
  });

  test('communications can be created + read back (PLAN §3 Coordinator)', async ({ request }) => {
    const message = {
      channel: 'global',
      from: 'Playwright',
      text: `Smoke test message ${Date.now()}`,
    };
    const createResponse = await request.post(apiUrl('/api/comms'), { data: message });
    expect(createResponse.status()).toBe(201);
    const created = await createResponse.json();
    expect(created.channel).toBe(message.channel);
    expect(created.text).toBe(message.text);

    const comms = await getJson<Array<{ id: string; text: string }>>(request, '/api/comms');
    expect(comms.find(entry => entry.id === created.id)).toBeDefined();

    const filtered = await getJson<Array<{ channel: string }>>(request, `/api/comms?channel=${message.channel}`);
    expect(filtered.length).toBeGreaterThan(0);
    filtered.forEach(entry => expect(entry.channel).toBe(message.channel));
  });

  test('damage index + gauges match Analyst view requirements (PLAN §3 Analyst)', async ({ request }) => {
    const damageIndex = await getJson<Array<{ zoneId: string; infra_index: number; human_index: number }>>(request, '/api/damage-index');
    expect(damageIndex.length).toBeGreaterThan(0);
    damageIndex.forEach(row => {
      expect(row.zoneId).toMatch(/^Z-/);
      expect(row.infra_index).toBeGreaterThanOrEqual(0);
      expect(row.infra_index).toBeLessThanOrEqual(1);
      expect(row.human_index).toBeGreaterThanOrEqual(0);
      expect(row.human_index).toBeLessThanOrEqual(1);
    });

    const gauges = await getJson<Array<{ id: string; level_m: number; trend: string }>>(request, '/api/gauges');
    expect(gauges.length).toBeGreaterThan(0);
    gauges.forEach(gauge => {
      expect(gauge.id).toMatch(/^G-/);
      expect(typeof gauge.level_m).toBe('number');
      expect(gauge.trend).toMatch(/rising|steady|falling/);
    });
  });

  test('plan endpoint returns assignments with actions (PLAN §3 Planner/Admin)', async ({ request }) => {
    const plan = await getJson<{
      version: string;
      assignments: Array<{ zoneId: string; actions: Array<Record<string, unknown>> }>;
      coverage: Record<string, unknown>;
      status: string;
    }>(request, '/api/plan');

    expect(typeof plan.version).toBe('string');
    expect(plan.assignments.length).toBeGreaterThan(0);
    plan.assignments.forEach(assignment => {
      expect(assignment.zoneId).toMatch(/^Z-/);
      expect(Array.isArray(assignment.actions)).toBe(true);
      expect(assignment.actions.length).toBeGreaterThan(0);
    });

    expect(plan.coverage).toBeTruthy();
    expect(plan.status).toBe('active');
  });

  test('planner can submit draft plan and retrieve it via status filter (PLAN §3 Planner)', async ({ request }) => {
    const payload = {
      name: `Playwright Draft ${Date.now()}`,
      planType: 'resource_deployment',
      assignments: [
        {
          zoneId: 'Z-ALFA',
          priority: 1,
          actions: [
            { type: 'deploy_pump', qty: 1, from: 'D-CENTRAL' },
            { type: 'assign_crew', crew: 'C-A1', task: 'validation' },
          ],
        },
      ],
      coverage: { total_zones: 1, covered_zones: 1, coverage_percentage: 100 },
      notes: 'Automated draft from Playwright',
    };

    const response = await request.post(apiUrl('/api/plan/draft'), { data: payload });
    expect(response.status()).toBe(201);
    const draft = await response.json();
    expect(draft.status).toBe('draft');
    expect(draft.assignments[0].zoneId).toBe(payload.assignments[0].zoneId);

    const fetchedDraft = await getJson<{
      status: string;
      assignments: Array<{ zoneId: string }>;
    }>(request, '/api/plan?status=draft');

    expect(fetchedDraft.status).toBe('draft');
    expect(fetchedDraft.assignments[0].zoneId).toBe(payload.assignments[0].zoneId);
  });

  test('CORS headers expose the API to the frontend', async ({ request }) => {
    const response = await request.get(apiUrl('/api/zones'));
    expect(response.headers()['access-control-allow-origin']).toBe('*');
  });
});
