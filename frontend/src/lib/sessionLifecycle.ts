export class SessionChangedError extends Error {
  constructor() {
    super('Session changed while refreshing authentication');
    this.name = 'SessionChangedError';
  }
}

let sessionRevision = 0;

export const markSessionChanged = () => {
  sessionRevision += 1;
};

export const captureSessionRevision = () => sessionRevision;

export const assertSessionUnchanged = (revision: number) => {
  if (revision !== sessionRevision) {
    throw new SessionChangedError();
  }
};

export const isSessionChangedError = (error: unknown) =>
  error instanceof SessionChangedError;
