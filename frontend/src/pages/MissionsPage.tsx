import { useState } from 'react';
import { Link } from '@tanstack/react-router';

import type { MissionDispatchResponse } from '../api/client';
import { OrderPreview } from '../components/missions/OrderPreview';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { useDispatchMission, useMissions } from '../hooks/useMissions';
import { MissionBuilderPage } from './MissionBuilderPage';

export function MissionsPage() {
  const missions = useMissions();
  const dispatch = useDispatchMission();
  const [publishedOrder, setPublishedOrder] = useState<MissionDispatchResponse>();

  const dispatchMission = async (missionId: string) => {
    const result = await dispatch.mutateAsync(missionId);
    setPublishedOrder(result);
  };

  return (
    <div className="grid gap-7">
      <header>
        <Badge className="mb-4 uppercase tracking-[0.14em]" variant="outline">Order workflow</Badge>
        <h1 className="m-0 text-5xl tracking-[-0.06em]">Missions</h1>
        <p className="mb-0 mt-3 text-muted-foreground">Plan graph routes and publish validated VDA 5050 orders.</p>
      </header>

      <section className="grid grid-cols-[360px_minmax(0,1fr)] items-start gap-4">
        <MissionBuilderPage />
        <MissionList
          dispatching={dispatch.isPending}
          missions={missions.data ?? []}
          onDispatch={dispatchMission}
        />
      </section>
      {dispatch.isError && <div className="rounded-xl border bg-card p-3 text-sm" role="alert">{dispatch.error.message}</div>}
      {publishedOrder && <OrderPreview payload={publishedOrder.payload} topic={publishedOrder.topic} />}
    </div>
  );
}

function MissionList({
  missions,
  dispatching,
  onDispatch,
}: {
  missions: Array<{
    id: string;
    startNodeKey: string;
    goalNodeKey: string;
    status: string;
    priority: number;
  }>;
  dispatching: boolean;
  onDispatch: (missionId: string) => Promise<void>;
}) {
  return (
    <Card className="rounded-2xl bg-card/80 shadow-none">
      <CardHeader>
        <CardTitle className="text-lg">Mission queue</CardTitle>
        <CardDescription>Assigned missions can be dispatched once.</CardDescription>
      </CardHeader>
      <CardContent>
        {missions.length === 0 ? (
          <div className="grid h-48 place-items-center rounded-xl border border-dashed text-sm text-muted-foreground">No missions created yet.</div>
        ) : (
          <div className="overflow-hidden rounded-xl border">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="border-b bg-muted/60 text-[0.68rem] uppercase tracking-[0.12em] text-muted-foreground">
                <tr><th className="px-4 py-3">Route</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Priority</th><th className="px-4 py-3 text-right">Action</th></tr>
              </thead>
              <tbody>
                {missions.map((mission) => (
                  <tr className="border-b last:border-b-0" key={mission.id}>
                    <td className="px-4 py-3"><strong>{mission.startNodeKey} → {mission.goalNodeKey}</strong><span className="block max-w-48 truncate font-mono text-[0.68rem] text-muted-foreground">{mission.id}</span></td>
                    <td className="px-4 py-3"><Badge variant={mission.status === 'sent' ? 'default' : 'outline'}>{mission.status}</Badge></td>
                    <td className="px-4 py-3">{mission.priority}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button asChild size="sm" variant="ghost">
                          <Link params={{ missionId: mission.id }} to="/missions/$missionId/live">Monitor</Link>
                        </Button>
                        <Button disabled={dispatching || mission.status !== 'assigned'} onClick={() => void onDispatch(mission.id)} size="sm" variant="outline">Dispatch</Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
