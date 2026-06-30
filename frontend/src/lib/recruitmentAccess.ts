import type { UserStatus } from '@/types';

const STORAGE_KEY = 'recruitment_access_token';
export const RECRUITMENT_ROUTE_PREFIX = '/recrutation';
const TOKEN_PATTERN = /^[a-f0-9]{64}$/;

export const isRecruitmentTokenShapeValid = (token: string | undefined): token is string =>
  Boolean(token && TOKEN_PATTERN.test(token));

export const storeRecruitmentAccessToken = (token: string) => {
  if (isRecruitmentTokenShapeValid(token)) {
    sessionStorage.setItem(STORAGE_KEY, token);
  }
};

export const getStoredRecruitmentAccessToken = () => {
  const token = sessionStorage.getItem(STORAGE_KEY) ?? undefined;
  return isRecruitmentTokenShapeValid(token) ? token : undefined;
};

export const clearRecruitmentAccessToken = () => {
  sessionStorage.removeItem(STORAGE_KEY);
};

export const getRecruitmentPath = (token: string) =>
  `${RECRUITMENT_ROUTE_PREFIX}/${token}`;

export const getStoredRecruitmentPath = () => {
  const token = getStoredRecruitmentAccessToken();
  return token ? getRecruitmentPath(token) : undefined;
};

export const destinationForUser = (status: UserStatus) =>
  status === 'new_volunteer'
    ? getStoredRecruitmentPath() ?? '/recruitment-required'
    : '/dashboard';
