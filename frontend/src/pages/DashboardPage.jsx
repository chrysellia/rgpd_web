import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { rgpdService } from '../services/api';
import Navbar from '../components/Navbar';
import { Shield, MessageSquare, ClipboardList,
         CheckCircle, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);

  useEffect(() => {
    rgpdService.status().then(r => setStatus(r.data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-6xl mx-auto p-6">

        {/* Bienvenue */}
        <div className="bg-gradient-to-r from-blue-900/40 to-blue-800/20
                        rounded-2xl p-6 mb-8 border border-blue-700/30">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-600 rounded-full flex
                            items-center justify-center text-2xl font-bold text-white">
              {user?.email?.[0]?.toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                Bienvenue, {user?.email}
              </h1>
              <p className="text-gray-400 mt-1">
                Plateforme de conformité RGPD — Agent IA
              </p>
            </div>
          </div>
        </div>

        {/* Statut système */}
        {status && (
          <div className={`flex items-center gap-2 px-4 py-3 rounded-xl mb-6
                           text-sm font-medium ${
            status.vectorstore_ready
              ? 'bg-green-900/30 border border-green-500/30 text-green-400'
              : 'bg-yellow-900/30 border border-yellow-500/30 text-yellow-400'
          }`}>
            {status.vectorstore_ready
              ? <><CheckCircle className="w-5 h-5" />
                  Base documentaire prête — Modèle : {status.ollama_model}</>
              : <><AlertCircle className="w-5 h-5" />
                  Base documentaire non initialisée — Lancez l'ingestion</>
            }
          </div>
        )}

        {/* Accès rapides */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link to="/chat" className="bg-gray-800 hover:bg-gray-750 border
                                      border-gray-700 hover:border-blue-500/50
                                      rounded-2xl p-6 transition-all group">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex
                              items-center justify-center group-hover:bg-blue-600/40
                              transition-colors">
                <MessageSquare className="w-6 h-6 text-blue-400" />
              </div>
              <h2 className="text-xl font-semibold text-white">Agent RGPD</h2>
            </div>
            <p className="text-gray-400 text-sm">
              Posez vos questions sur la conformité RGPD, les obligations
              réglementaires et les bonnes pratiques.
            </p>
          </Link>

          <Link to="/traitement" className="bg-gray-800 hover:bg-gray-750 border
                                            border-gray-700 hover:border-green-500/50
                                            rounded-2xl p-6 transition-all group">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-green-600/20 rounded-xl flex
                              items-center justify-center group-hover:bg-green-600/40
                              transition-colors">
                <ClipboardList className="w-6 h-6 text-green-400" />
              </div>
              <h2 className="text-xl font-semibold text-white">
                Analyse de Traitement
              </h2>
            </div>
            <p className="text-gray-400 text-sm">
              Soumettez un traitement de données pour obtenir une analyse
              de conformité RGPD détaillée.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}