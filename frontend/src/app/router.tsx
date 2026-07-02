import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router';

import { App } from '../App';
import { DashboardPage } from '../pages/DashboardPage';
import { MapPage } from '../pages/MapPage';
import { MissionLivePage } from '../pages/MissionLivePage';
import { MissionsPage } from '../pages/MissionsPage';
import { MqttLogsPage } from '../pages/MqttLogsPage';
import { PlaceholderPage } from '../pages/PlaceholderPage';
import { RobotDetailPage } from '../pages/RobotDetailPage';
import { RobotsPage } from '../pages/RobotsPage';

const rootRoute = createRootRoute({ component: App });
const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
});
const robotsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/robots',
  component: RobotsPage,
});
const robotDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/robots/$robotId',
  component: RobotDetailPage,
});
const mapRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/map',
  component: MapPage,
});
const missionsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/missions',
  component: MissionsPage,
});
const missionLiveRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/missions/$missionId/live',
  component: MissionLivePage,
});
const mqttLogsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/mqtt',
  component: MqttLogsPage,
});

const placeholders = [
  ['/traffic', 'Traffic'],
  ['/settings', 'Settings'],
] as const;
const placeholderRoutes = placeholders.map(([path, title]) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <PlaceholderPage title={title} />,
  }),
);

export const routeTree = rootRoute.addChildren([
  dashboardRoute,
  robotsRoute,
  robotDetailRoute,
  mapRoute,
  missionsRoute,
  missionLiveRoute,
  mqttLogsRoute,
  ...placeholderRoutes,
]);

export const router = createRouter({ routeTree, defaultPreload: 'intent' });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
