import { useState } from 'react';
import { rgpdService } from '../services/api';
import Navbar from '../components/Navbar';
import { ClipboardList, CheckCircle, AlertTriangle, Loader } from 'lucide-react';

export default function TraitementPage() {
  const [form, setForm] = useState({
    nom: '',
    finalite: '',
    base_legale: '',
    categories_donnees: '',
    destinataires: '',
    duree_conservation: '',
    transferts_hors_ue: false
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const basesLegales = [
    'Consentement',
    'Contrat',
    'Obligation légale',
    'Sauvegarde des intérêts vitaux',
    'Mission d\'intérêt public',
    'Intérêts légitimes'
  ];

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await rgpdService.analyserTraitement(form);
      setResult(response.data);
    } catch (err) {
      setResult({
        analyse: 'Erreur lors de l\'analyse. Vérifiez que le backend est actif.',
        sources: []
      });
    } finally {
      setLoading(false);
    }
  };

  const inputClass = `w-full px-4 py-3 bg-gray-800 border border-gray-700
    rounded-xl text-white placeholder-gray-400
    focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500`;

  const labelClass = "block text-sm font-medium text-gray-300 mb-2";

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-4xl mx-auto p-6">

        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
          <ClipboardList className="w-7 h-7 text-blue-400" />
          Analyse de Traitement RGPD
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Formulaire */}
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">
              Informations du traitement
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">

              <div>
                <label className={labelClass}>Nom du traitement *</label>
                <input name="nom" value={form.nom} onChange={handleChange}
                  placeholder="Ex: Gestion des ressources humaines"
                  required className={inputClass} />
              </div>

              <div>
                <label className={labelClass}>Finalité *</label>
                <textarea name="finalite" value={form.finalite}
                  onChange={handleChange} rows={3} required
                  placeholder="Objectif du traitement..."
                  className={inputClass + " resize-none"} />
              </div>

              <div>
                <label className={labelClass}>Base légale *</label>
                <select name="base_legale" value={form.base_legale}
                  onChange={handleChange} required className={inputClass}>
                  <option value="">Sélectionner...</option>
                  {basesLegales.map(b => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelClass}>Catégories de données *</label>
                <textarea name="categories_donnees"
                  value={form.categories_donnees} onChange={handleChange}
                  rows={2} required
                  placeholder="Nom, prénom, email, données de santé..."
                  className={inputClass + " resize-none"} />
              </div>

              <div>
                <label className={labelClass}>Destinataires</label>
                <input name="destinataires" value={form.destinataires}
                  onChange={handleChange}
                  placeholder="DRH, prestataires, organismes publics..."
                  className={inputClass} />
              </div>

              <div>
                <label className={labelClass}>Durée de conservation *</label>
                <input name="duree_conservation"
                  value={form.duree_conservation} onChange={handleChange}
                  placeholder="Ex: 5 ans après fin du contrat"
                  required className={inputClass} />
              </div>

              <div className="flex items-center gap-3">
                <input type="checkbox" name="transferts_hors_ue"
                  checked={form.transferts_hors_ue} onChange={handleChange}
                  className="w-5 h-5 rounded border-gray-600 bg-gray-700
                             text-blue-600 focus:ring-blue-500" />
                <label className="text-sm text-gray-300">
                  Transferts de données hors UE
                </label>
              </div>

              <button type="submit" disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700
                           disabled:bg-gray-700 text-white font-semibold
                           rounded-xl transition-colors flex items-center
                           justify-center gap-2">
                {loading
                  ? <><Loader className="w-5 h-5 animate-spin" />Analyse en cours...</>
                  : <><CheckCircle className="w-5 h-5" />Analyser la conformité</>
                }
              </button>
            </form>
          </div>

          {/* Résultat */}
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              Analyse de conformité
            </h2>

            {!result && !loading && (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <p className="text-center">
                  Remplissez le formulaire et cliquez sur<br/>
                  "Analyser la conformité"
                </p>
              </div>
            )}

            {loading && (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <Loader className="w-10 h-10 text-blue-400 animate-spin mx-auto mb-3" />
                  <p className="text-gray-400">L'agent analyse le traitement...</p>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="bg-gray-900 rounded-xl p-4 border border-gray-700
                                max-h-96 overflow-y-auto">
                  <p className="text-gray-100 text-sm whitespace-pre-wrap leading-relaxed">
                    {result.analyse}
                  </p>
                </div>
                {result.sources?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">Sources :</p>
                    <div className="flex flex-wrap gap-2">
                      {result.sources.map((src, i) => (
                        <span key={i} className="text-xs bg-gray-700
                                                  text-blue-300 rounded px-2 py-1">
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}