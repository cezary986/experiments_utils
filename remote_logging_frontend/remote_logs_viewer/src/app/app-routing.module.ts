import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';
import { AuthGuardService } from './auth/services/auth-guard.service';

const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./auth/auth.module').then((m) => m.AuthModule),
  },
  {
    path: 'experiments',
    loadChildren: () =>
      import('./main/experiments/experiments.module').then(
        (m) => m.ExperimentsModule
      ),
    canActivate: [AuthGuardService],
  },
  {
    path: 'experiments/:id/runs',
    loadChildren: () =>
      import('./main/runs/runs.module').then((m) => m.RunsModule),
    canActivate: [AuthGuardService],
  },
  {
    path: 'experiments/:id/runs/:runId',
    loadChildren: () =>
      import('./main/run/run.module').then((m) => m.RunModule),
    canActivate: [AuthGuardService],
  },
  {
    path: '',
    redirectTo: 'experiments',
    pathMatch: 'full',
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule {}
