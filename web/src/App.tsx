import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import Layout from "./components/Layout";
import AccountDetailPage from "./pages/AccountDetailPage";
import AccountsPage from "./pages/AccountsPage";
import CategoriesPage from "./pages/CategoriesPage";
import DashboardPage from "./pages/DashboardPage";
import EntriesPage from "./pages/EntriesPage";
import EntryFormPage from "./pages/EntryFormPage";
import ImportPage from "./pages/ImportPage";
import LoginPage from "./pages/LoginPage";
import PeoplePage from "./pages/PeoplePage";
import PlatformsPage from "./pages/PlatformsPage";
import VendorsPage from "./pages/VendorsPage";

function ProtectedRoutes() {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/people" element={<PeoplePage />} />
        <Route path="/platforms" element={<PlatformsPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/accounts/:id" element={<AccountDetailPage />} />
        <Route path="/entries" element={<EntriesPage />} />
        <Route path="/entries/new" element={<EntryFormPage />} />
        <Route path="/entries/import" element={<ImportPage />} />
        <Route path="/entries/:id" element={<EntryFormPage />} />
        <Route path="/vendors" element={<VendorsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedRoutes />} />
      </Routes>
    </AuthProvider>
  );
}
