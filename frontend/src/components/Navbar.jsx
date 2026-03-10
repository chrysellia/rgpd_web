import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, MessageSquare, ClipboardList,
         LayoutDashboard, LogOut } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/chat', icon: MessageSquare, label: 'Agent RGPD' },
    { path: '/traitement', icon: ClipboardList, label: 'Traitement' },
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">

        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <Shield className="w-7 h-7 text-blue-400" />
            <span className="text-white font-bold text-lg">Agent RGPD</span>
          </Link>
          <div className="flex items-center gap-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link key={path} to={path}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg
                            text-sm font-medium transition-colors ${
                  location.pathname === path
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}>
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm">{user?.email}</span>
          <button onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-gray-400
                       hover:text-white hover:bg-gray-700 rounded-lg
                       text-sm transition-colors">
            <LogOut className="w-4 h-4" />
            Déconnexion
          </button>
        </div>
      </div>
    </nav>
  );
}