import { Navigate, Outlet } from 'react-router-dom';
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
  if (permissionQuery.isLoading) {
    return <div className="p-8 text-center text-sm text-gray-500">Sprawdzanie uprawnień…</div>;
  }
  const effective = permissionQuery.data?.permissions ?? [];
  const isAllowed = requiredPermission
    ? effective.includes(requiredPermission)
    : requiredAnyPermission?.some((permission) => effective.includes(permission)) ?? true;
  if (!isAllowed) {
    return (
      <div className="p-8 text-center">
        <h1 className="text-xl font-bold text-gray-900">Brak dostępu</h1>
        <p className="mt-2 text-sm text-gray-500">Nie masz uprawnienia wymaganego do tej sekcji.</p>
      </div>
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;
