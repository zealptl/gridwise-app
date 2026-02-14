import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import TeamCreate from '@/pages/TeamCreate'
import TeamDetail from '@/pages/TeamDetail'
import TeamEdit from '@/pages/TeamEdit'
import RulesAdmin from '@/pages/RulesAdmin'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/teams/create" element={<TeamCreate />} />
          <Route path="/teams/:id" element={<TeamDetail />} />
          <Route path="/teams/:id/edit" element={<TeamEdit />} />
          <Route path="/admin/rules" element={<RulesAdmin />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
