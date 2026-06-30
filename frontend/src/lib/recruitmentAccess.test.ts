import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearRecruitmentAccessToken,
  destinationForUser,
  getStoredRecruitmentAccessToken,
  getStoredRecruitmentPath,
  storeRecruitmentAccessToken,
} from './recruitmentAccess';

const token = 'a'.repeat(64);

describe('recruitment access context', () => {
  beforeEach(() => sessionStorage.clear());

  it('stores only an opaque token and rebuilds the public path', () => {
    storeRecruitmentAccessToken(token);

    expect(getStoredRecruitmentAccessToken()).toBe(token);
    expect(getStoredRecruitmentPath()).toBe(`/recrutation/${token}`);
  });

  it('does not redirect a normally registered user to recruitment', () => {
    storeRecruitmentAccessToken(token);

    expect(destinationForUser('regular')).toBe('/dashboard');
    expect(destinationForUser('new_volunteer')).toBe(`/recrutation/${token}`);
  });

  it('can remove invite context after a regular user signs in', () => {
    storeRecruitmentAccessToken(token);

    clearRecruitmentAccessToken();

    expect(getStoredRecruitmentAccessToken()).toBeUndefined();
  });
});
