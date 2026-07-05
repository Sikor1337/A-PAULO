import { Navigate, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useMyPermissions } from '@/hooks/usePermissions';
import { destinationForUser } from '@/lib/recruitmentAccess';
import type { PermissionCode, UserStatus } from '@/types';

interface Props {
  allowedStatuses?: UserStatus[];
  requiredPermission?: PermissionCode;
  requiredAnyPermission?: PermissionCode[];
}

const ProtectedRoute = ({ allowedStatuses, requiredPermission, requiredAnyPermission }: Props) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedStatuses && !allowedStatuses.includes(user.status)) {
    return <Navigate to={destinationForUser(user.status)} replace />;
  }
  if (requiredPermission || requiredAnyPermission?.length) {
    return (
      <PermissionBoundary
        requiredPermission={requiredPermission}
        requiredAnyPermission={requiredAnyPermission}
      />
    );
  }

  return <Outlet />;
};

const PermissionBoundary = ({ requiredPermission, requiredAnyPermission }: Omit<Props, 'allowedStatuses'>) => {
  const permissionQuery = useMyPermissions();
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  if (permissionQuery.isLoading) {
    return <div className="p-8 text-center text-sm text-gray-500">Sprawdzanie uprawnień…</div>;
  }
  const effective = permissionQuery.data?.permissions ?? [];
  const isAllowed = requiredPermission
    ? effective.includes(requiredPermission)
    : requiredAnyPermission?.some((permission) => effective.includes(permission)) ?? true;
  if (!isAllowed) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[#1e2330] p-4">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
          <h1 className="text-2xl font-bold text-gray-950">Brak dostępu</h1>
          <p className="mt-3 text-base leading-6 text-gray-700">
            To konto nie ma uprawnienia wymaganego do tej sekcji.
          </p>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            className="mt-6 min-h-11 w-full rounded-lg bg-indigo-600 px-5 py-3 font-bold text-white hover:bg-indigo-700"
          >
            Wyloguj i zmień konto
          </button>
        </div>
      </div>
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;
