import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Mail, Lock, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Email ou mot de passe incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20
                          bg-blue-600 rounded-full mb-4">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Agent RGPD</h1>
          <p className="text-gray-400 mt-2">
            Plateforme de conformité intelligente
          </p>
        </div>

        {/* Formulaire */}
        <div className="bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2
                                 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="dpo@entreprise.com"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600
                             rounded-xl text-white placeholder-gray-400
                             focus:outline-none focus:border-blue-500
                             focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Mot de passe */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2
                                 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600
                             rounded-xl text-white placeholder-gray-400
                             focus:outline-none focus:border-blue-500
                             focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Erreur */}
            {error && (
              <div className="flex items-center gap-2 bg-red-900/30 border
                              border-red-500/50 rounded-xl p-3">
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {/* Bouton */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700
                         disabled:bg-gray-600 text-white font-semibold
                         rounded-xl transition-colors duration-200"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>

            <div className="flex justify-between items-center mt-4">
              <Link
                to="/forgot-password"
                className="text-sm text-gray-400 hover:text-blue-400 transition-colors"
              >
                Mot de passe oublié ?
              </Link>
              <Link
                to="/register"
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                Créer un compte
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}