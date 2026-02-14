import { Link } from 'react-router-dom'
import { Trophy } from 'lucide-react'

export const Header = () => {
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Trophy className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">GridWise</span>
        </Link>

        <nav className="flex items-center gap-6">
          <Link to="/" className="text-sm font-medium hover:text-primary">
            Teams
          </Link>
          <Link to="/admin/rules" className="text-sm font-medium hover:text-primary">
            Rules
          </Link>
        </nav>
      </div>
    </header>
  )
}
