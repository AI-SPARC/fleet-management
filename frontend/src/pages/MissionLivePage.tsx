import { useEffect, useState, type ReactNode } from 'react';
import { Link, useParams } from '@tanstack/react-router';

import type { RobotState } from '../api/client';
import { MapGraph } from '../components/map/MapGraph';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { useMap } from '../hooks/useMaps';
import { useMission, useMissionRoute } from '../hooks/useMissions';
import { useRobot, useRobotState } from '../hooks/useRobots';

const STALE_AFTER_MS = 10_000;

export function MissionLivePage() {
  const { missionId } = useParams({ from: '/missions/$missionId/live' });
  const mission = useMission(missionId);
  const map = useMap(mission.data?.mapId ?? undefined);
  const robot = useRobot(mission.data?.assignedRobotId ?? undefined);
  const state = useRobotState(mission.data?.assignedRobotId ?? undefined);
  const route = useMissionRoute(
    missionId,
    mission.data?.mapId,
    mission.data?.startNodeKey,
    mission.data?.goalNodeKey,
  );
  const now = useNow();
  const stateAge = telemetryAge(state.data, now);
  const stale = stateAge === undefined || stateAge > STALE_AFTER_MS;
  const belongsToMission = state.data?.orderId === missionId;
  const routeNodes = route.data?.nodeKeys ?? [];
  const routeIndex = state.data?.lastNodeId
    ? routeNodes.indexOf(state.data.lastNodeId)
    : -1;

  if (mission.isLoading) return <LivePlaceholder text="Loading mission…" />;
  if (mission.isError || !mission.data) return <LivePlaceholder text="Mission not found." />;

  return (
    <div className="grid gap-7">
      <header className="flex items-end justify-between gap-6">
        <div>
          <Badge className="mb-4 uppercase tracking-[0.14em]" variant="outline">
            Live execution
          </Badge>
          <h1 className="m-0 text-5xl tracking-[-0.06em]">Mission monitor</h1>
          <p className="mb-0 mt-3 font-mono text-xs text-muted-foreground">{missionId}</p>
        </div>
        <Button asChild variant="outline">
          <Link to="/missions">Back to missions</Link>
        </Button>
      </header>

      <section className="grid grid-cols-4 gap-3">
        <Metric label="Mission" value={mission.data.status} />
        <Metric label="Connection" value={robot.data?.lastConnectionState ?? 'UNKNOWN'} />
        <Metric
          label="Telemetry"
          tone={stale ? 'danger' : 'normal'}
          value={stateAge === undefined ? 'No data' : stale ? `Stale · ${formatAge(stateAge)}` : 'Live'}
        />
        <Metric
          label="Battery"
          value={state.data?.batteryCharge == null ? '—' : `${state.data.batteryCharge.toFixed(1)}%`}
        />
      </section>

      {!belongsToMission && state.data && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          Latest robot state belongs to order {state.data.orderId ?? 'none'}, not this mission.
        </div>
      )}

      {map.data ? (
        <MapGraph
          highlightedNodeKeys={routeNodes}
          map={map.data}
          robots={robot.data && state.data ? [{ robot: robot.data, state: state.data }] : []}
        />
      ) : (
        <LivePlaceholder text="Loading calibrated map…" />
      )}

      <section className="grid grid-cols-3 gap-4">
        <DetailCard title="Route">
          <p className="m-0 text-sm">
            {mission.data.startNodeKey} → {mission.data.goalNodeKey}
          </p>
          <p className="mb-0 mt-2 text-xs text-muted-foreground">
            {route.isError
              ? 'Route is currently unavailable.'
              : routeIndex >= 0
                ? `${routeIndex + 1} of ${routeNodes.length} nodes reached`
                : `${routeNodes.length} planned nodes`}
          </p>
        </DetailCard>
        <DetailCard title="Robot state">
          <p className="m-0 text-sm">Last node: {state.data?.lastNodeId ?? '—'}</p>
          <p className="mb-0 mt-2 text-xs text-muted-foreground">
            Mode: {state.data?.operatingMode ?? 'unknown'} · Order: {state.data?.orderId ?? 'none'}
          </p>
        </DetailCard>
        <DetailCard title="Safety & errors">
          <p className="m-0 text-sm">{state.data?.errors?.length ?? 0} active errors</p>
          <p className="mb-0 mt-2 text-xs text-muted-foreground">
            {safetyLabel(state.data)}
          </p>
        </DetailCard>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = 'normal',
}: {
  label: string;
  value: string;
  tone?: 'normal' | 'danger';
}) {
  return (
    <Card className={tone === 'danger' ? 'border-red-300 bg-red-50 shadow-none' : 'shadow-none'}>
      <CardContent className="p-4">
        <span className="text-xs text-muted-foreground">{label}</span>
        <strong className="mt-1 block text-lg">{value}</strong>
      </CardContent>
    </Card>
  );
}

function DetailCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="shadow-none">
      <CardHeader><CardTitle className="text-base">{title}</CardTitle></CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function LivePlaceholder({ text }: { text: string }) {
  return <div className="grid h-64 place-items-center rounded-2xl border border-dashed text-sm text-muted-foreground">{text}</div>;
}

function useNow() {
  const [now, setNow] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 5_000);
    return () => window.clearInterval(timer);
  }, []);
  return now;
}

function telemetryAge(state: RobotState | undefined, now: number): number | undefined {
  const timestamp = state?.receivedAt ?? readTimestamp(state?.rawPayload);
  if (!timestamp) return undefined;
  const receivedAt = Date.parse(timestamp);
  return Number.isNaN(receivedAt) ? undefined : Math.max(0, now - receivedAt);
}

function readTimestamp(payload: Record<string, unknown> | undefined): string | undefined {
  return typeof payload?.timestamp === 'string' ? payload.timestamp : undefined;
}

function formatAge(age: number): string {
  return `${Math.round(age / 1000)}s ago`;
}

function safetyLabel(state: RobotState | undefined): string {
  const safety = state?.safetyState;
  if (!safety) return 'No safety state reported';
  const eStop = typeof safety.eStop === 'string' ? safety.eStop : 'unknown';
  const fieldViolation = safety.fieldViolation === true ? 'field violation' : 'field clear';
  return `E-stop: ${eStop} · ${fieldViolation}`;
}
