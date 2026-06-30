import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import BeneficiariesPage from './pages/BeneficiariesPage';
import BOCardsPage from './pages/BOCardsPage';
import VolunteersPage from './pages/VolunteersPage';
import GroupsPage from './pages/GroupsPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import EventsPage from './pages/EventsPage';
import RecruitmentLayout from './pages/recruitment/RecruitmentLayout';
import RecruitmentFormBuilderPage from './pages/recruitment/RecruitmentFormBuilderPage';
import RecruitmentResponsesPage from './pages/recruitment/RecruitmentResponsesPage';
import RecruitmentOnboardingPage from './pages/recruitment/RecruitmentOnboardingPage';
import RecruitmentApplicationPage from './pages/recruitment/RecruitmentApplicationPage';
import { authService } from './services/authService';
import { useAuthStore } from './stores/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const SessionProfileSync = () => {
  const { isAuthenticated, updateUser } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    authService.getUserProfile()
      .then((profile) => {
        if (!active) return;
        updateUser({
          id: profile.id,
          email: profile.email,
          first_name: profile.first_name || '',
          last_name: profile.last_name || '',
          status: profile.status,
        });
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [isAuthenticated, updateUser]);

  return null;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProfileSync />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute allowedStatuses={['new_volunteer']} />}>
            <Route path="/recruitment/apply" element={<RecruitmentApplicationPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedStatuses={['regular', 'admin']} />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/beneficiaries" element={<BeneficiariesPage />} />
            <Route path="/bo-cards" element={<BOCardsPage />} />
            <Route path="/volunteers" element={<VolunteersPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/recruitment" element={<RecruitmentLayout />}>
              <Route index element={<Navigate to="form" replace />} />
              <Route path="form" element={<RecruitmentFormBuilderPage />} />
              <Route path="responses" element={<RecruitmentResponsesPage />} />
              <Route path="onboarding" element={<RecruitmentOnboardingPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
