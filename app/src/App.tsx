import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { AuthGuard } from '@/components/auth/AuthGuard'
import Dashboard from '@/pages/Dashboard'
import TeamCreate from '@/pages/TeamCreate'
import TeamDetail from '@/pages/TeamDetail'
import TeamEdit from '@/pages/TeamEdit'
import RulesAdmin from '@/pages/RulesAdmin'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Advisor from '@/pages/Advisor'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth routes — no layout chrome */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes inside shared layout */}
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/teams/create" element={<TeamCreate />} />
          <Route path="/teams/:id" element={<TeamDetail />} />
          <Route path="/teams/:id/edit" element={<TeamEdit />} />
          <Route path="/admin/rules" element={<RulesAdmin />} />
          <Route
            path="/advisor"
            element={
              <AuthGuard>
                <Advisor />
              </AuthGuard>
            }
          />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
