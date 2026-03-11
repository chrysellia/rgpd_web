import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '../services/api';
import { Shield, Mail, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1); // 1: email, 2: token+nouveau mdp
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [devToken, setDevToken] = useState(''); // Token affiché en dev

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await authService.forgotPassword(email);
      setDevToken(response.data.reset_token || '');
      setSuccess(response.data.message);
      setStep(2);
    } catch (err) {
      setError('Erreur lors de la demande de réinitialisation.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    setLoading(true);
    try {
      await authService.resetPassword(token, newPassword);
      setSuccess('Mot de passe réinitialisé ! Vous pouvez maintenant vous connecter.');
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Token invalide ou expiré.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = `w-full px-4 py-3 bg-gray-700 border border-gray-600
    rounded-xl text-white placeholder-gray-400
    focus:outline-none focus:border-blue-500`;

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20
                          bg-blue-600 rounded-full mb-4">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">
            {step === 1 ? 'Mot de passe oublié' : 'Réinitialisation'}
          </h1>
          <p className="text-gray-400 mt-2">Agent RGPD</p>
        </div>

        <div className="bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-700">

          {/* Étape 1 — Saisie email */}
          {step === 1 && (
            <form onSubmit={handleForgotPassword} className="space-y-5">
              <p className="text-gray-400 text-sm">
                Entrez votre email pour recevoir un lien de réinitialisation.
              </p>
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
                    className="w-full pl-10 pr-4 py-3 bg-gray-700 border
                               border-gray-600 rounded-xl text-white
                               placeholder-gray-400 focus:outline-none
                               focus:border-blue-500"
                  />
                </div>
              </div>
              {error && (
                <div className="flex items-center gap-2 bg-red-900/30
                                border border-red-500/50 rounded-xl p-3">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700
                           disabled:bg-gray-600 text-white font-semibold
                           rounded-xl transition-colors"
              >
                {loading ? 'Envoi...' : 'Envoyer le lien'}
              </button>
            </form>
          )}

          {/* Étape 2 — Token + nouveau mdp */}
          {step === 2 && (
            <form onSubmit={handleResetPassword} className="space-y-5">
              <div className="bg-green-900/30 border border-green-500/50
                              rounded-xl p-3">
                <p className="text-green-400 text-sm">{success}</p>
              </div>

              {/* Token affiché en développement */}
              {devToken && (
                <div className="bg-yellow-900/30 border border-yellow-500/50
                                rounded-xl p-3">
                  <p className="text-yellow-400 text-xs font-mono">
                    Token (dev uniquement) : {devToken}
                  </p>
                  <button
                    type="button"
                    onClick={() => setToken(devToken)}
                    className="text-yellow-300 text-xs underline mt-1"
                  >
                    Utiliser ce token
                  </button>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Token de réinitialisation
                </label>
                <input
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Collez votre token ici"
                  required
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Confirmer le mot de passe
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className={inputClass}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 bg-red-900/30
                                border border-red-500/50 rounded-xl p-3">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700
                           disabled:bg-gray-600 text-white font-semibold
                           rounded-xl transition-colors"
              >
                {loading ? 'Réinitialisation...' : 'Réinitialiser le mot de passe'}
              </button>
            </form>
          )}

          {/* Étape 3 — Succès */}
          {step === 3 && (
            <div className="text-center space-y-4">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto" />
              <p className="text-white font-semibold text-lg">
                Mot de passe réinitialisé !
              </p>
              <p className="text-gray-400 text-sm">{success}</p>
              <Link
                to="/login"
                className="block w-full py-3 bg-blue-600 hover:bg-blue-700
                           text-white font-semibold rounded-xl text-center
                           transition-colors"
              >
                Se connecter
              </Link>
            </div>
          )}

          {step !== 3 && (
            <Link
              to="/login"
              className="flex items-center justify-center gap-2
                         text-gray-400 hover:text-white text-sm mt-6
                         transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}