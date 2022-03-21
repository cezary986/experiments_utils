import { Injectable } from '@angular/core';
import { Action, State, StateContext } from '@ngxs/store';
import { User } from 'src/app/common/models/user.model';

export class SetCurrentUser {
  static readonly type = '[USER] SetCurrentUser';
  constructor(public payload: User) {}
}

@State<User>({
  name: 'user',
  defaults: null,
})
@Injectable()
export class CurrentUserState {
  @Action(SetCurrentUser)
  setCurrentUser(
    { getState, patchState, setState }: StateContext<User>,
    { payload }: SetCurrentUser
  ): void {
    setState(payload);
  }
}
