import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { UserStatus } from '@/types';
import { destinationForUser } from '@/lib/recruitmentAccess';

interface Props {
  allowedStatuses?: UserStatus[];
}

const ProtectedRoute = ({ allowedStatuses }: Props) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedStatuses && !allowedStatuses.includes(user.status)) {
    return <Navigate to={destinationForUser(user.status)} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
