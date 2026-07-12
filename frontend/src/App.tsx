import { useEffect } from 'react';
import {
  Navigate,
  Outlet,
  Route,
  RouterProvider,
  createBrowserRouter,
  createRoutesFromElements,
} from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import BackendWakeupPopup from './components/BackendWakeupPopup';
import AppDialogProvider from './components/ui/AppDialogProvider';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import BeneficiariesPage from './pages/BeneficiariesPage';
import BOCardsPage from './pages/BOCardsPage';
import VolunteersPage from './pages/VolunteersPage';
import GroupsPage from './pages/GroupsPage';
import DepartmentsPage from './pages/DepartmentsPage';
import BugReportsPage from './pages/BugReportsPage';
import TasksPage from './pages/TasksPage';
import ProfilePage from './pages/ProfilePage';
import MyDepartureSurveyPage from './pages/MyDepartureSurveyPage';
import SettingsPage from './pages/SettingsPage';
import EventsPage from './pages/EventsPage';
import PapCalendarPage from './pages/PapCalendarPage';
import RecruitmentLayout from './pages/recruitment/RecruitmentLayout';
import RecruitmentFormBuilderPage from './pages/recruitment/RecruitmentFormBuilderPage';
import RecruitmentResponsesPage from './pages/recruitment/RecruitmentResponsesPage';
import RecruitmentOnboardingPage from './pages/recruitment/RecruitmentOnboardingPage';
import DepartureEditorPage from './pages/recruitment/DepartureEditorPage';
import DepartureResponsesPage from './pages/recruitment/DepartureResponsesPage';
import RecruitmentEntryPage from './pages/recruitment/RecruitmentEntryPage';
import RecruitmentAccessRequiredPage from './pages/recruitment/RecruitmentAccessRequiredPage';
import BeneficiaryApplicationPage from './pages/recruitment/BeneficiaryApplicationPage';
import BeneficiaryRecruitmentEditorPage from './pages/recruitment/BeneficiaryRecruitmentEditorPage';
import BeneficiaryRecruitmentResponsesPage from './pages/recruitment/BeneficiaryRecruitmentResponsesPage';
import { queryClient } from './lib/queryClient';
import { authService } from './services/authService';
import { useAuthStore } from './stores/authStore';

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

const operationalPermissions = [
  'CAN_VIEW_VOLUNTEERS',
  'CAN_VIEW_BENEFICIARIES',
  'CAN_VIEW_PI_GROUPS',
  'CAN_VIEW_ATTACHMENTS',
  'CAN_VIEW_RECRUITMENT',
  'CAN_VIEW_EVENTS',
  'CAN_VIEW_USERS',
  'CAN_VIEW_SECURITY',
] as const;

const AppLayout = () => (
  <>
    <SessionProfileSync />
    <BackendWakeupPopup />
    <Outlet />
  </>
);

const router = createBrowserRouter(createRoutesFromElements(
  <Route element={<AppLayout />}>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/recrutation/:token" element={<RecruitmentEntryPage />} />
    <Route path="/beneficiary-application/:token" element={<BeneficiaryApplicationPage />} />
    <Route element={<ProtectedRoute allowedStatuses={['new_volunteer']} />}>
      <Route path="/recruitment-required" element={<RecruitmentAccessRequiredPage />} />
    </Route>

    <Route element={<ProtectedRoute allowedStatuses={['regular', 'admin']} />}>
      <Route element={<ProtectedRoute requiredAnyPermission={[...operationalPermissions]} />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_BENEFICIARIES" />}>
        <Route path="/beneficiaries" element={<BeneficiariesPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_ATTACHMENTS" />}>
        <Route path="/bo-cards" element={<BOCardsPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_VOLUNTEERS" />}>
        <Route path="/volunteers" element={<VolunteersPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_PI_GROUPS" />}>
        <Route path="/groups" element={<GroupsPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_DEPARTMENTS" />}>
        <Route path="/departments" element={<DepartmentsPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_TASKS" />}>
        <Route path="/tasks" element={<TasksPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_EVENTS" />}>
        <Route path="/pap-calendar" element={<PapCalendarPage />} />
        <Route path="/events" element={<EventsPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_SUBMIT_DEPARTURE_SURVEY" />}>
        <Route path="/departure-survey" element={<MyDepartureSurveyPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_SUBMIT_BUG_REPORTS" />}>
        <Route path="/bug-reports" element={<BugReportsPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredAnyPermission={['CAN_VIEW_USERS', 'CAN_VIEW_SECURITY']} />}>
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route element={<ProtectedRoute requiredPermission="CAN_VIEW_RECRUITMENT" />}>
        <Route path="/recruitment" element={<RecruitmentLayout />}>
          <Route index element={<Navigate to="surveys/recruitment/editor" replace />} />
          <Route path="surveys/recruitment/editor" element={<RecruitmentFormBuilderPage />} />
          <Route path="surveys/recruitment/responses" element={<RecruitmentResponsesPage />} />
          <Route path="surveys/departure/editor" element={<DepartureEditorPage />} />
          <Route path="surveys/departure/responses" element={<DepartureResponsesPage />} />
          <Route path="surveys/beneficiary/editor" element={<BeneficiaryRecruitmentEditorPage />} />
          <Route path="surveys/beneficiary/responses" element={<BeneficiaryRecruitmentResponsesPage />} />
          <Route path="onboarding" element={<RecruitmentOnboardingPage />} />
          {/* Back-compat redirects for old bookmarks. */}
          <Route path="form" element={<Navigate to="/recruitment/surveys/recruitment/editor" replace />} />
          <Route path="responses" element={<Navigate to="/recruitment/surveys/recruitment/responses" replace />} />
          <Route path="departures" element={<Navigate to="/recruitment/surveys/departure/editor" replace />} />
        </Route>
      </Route>
    </Route>

    <Route path="*" element={<Navigate to="/" replace />} />
  </Route>,
));

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppDialogProvider>
        <RouterProvider router={router} />
      </AppDialogProvider>
    </QueryClientProvider>
  );
}

export default App;
