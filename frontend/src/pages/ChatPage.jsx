import { useState, useRef, useEffect } from 'react';
import { rgpdService } from '../services/api';
import Navbar from '../components/Navbar';
import { Send, Bot, User, FileText, Loader,
         History, ChevronDown, ChevronUp } from 'lucide-react';

const DOMAINES = [
  { value: 'general', label: '🌐 Général', desc: 'Toutes organisations' },
  { value: 'sante', label: '🏥 Santé', desc: 'Données médicales' },
  { value: 'rh', label: '👥 Ressources Humaines', desc: 'Données employés' },
  { value: 'education', label: '🎓 Éducation', desc: 'Données élèves' },
  { value: 'finance', label: '💰 Finance', desc: 'Données bancaires' },
  { value: 'commerce', label: '🛒 Commerce', desc: 'Données clients' },
  { value: 'juridique', label: '⚖️ Juridique', desc: 'Données juridiques' },
  { value: 'industrie', label: '🏭 Industrie', desc: 'Données industrielles' },
];

const SUGGESTIONS = {
  general: [
    "Quelles sont les obligations du DPO ?",
    "Comment rédiger une politique de confidentialité ?",
    "Qu'est-ce que le registre des traitements ?",
  ],
  sante: [
    "Quelle est la durée de conservation d'un dossier médical ?",
    "Quelles données de santé sont considérées sensibles ?",
    "Comment gérer le consentement patient ?",
  ],
  rh: [
    "Quelles données salarié puis-je conserver ?",
    "Quelle est la base légale pour traiter les données RH ?",
    "Comment gérer les données de candidature ?",
  ],
  finance: [
    "Quelle durée de conservation pour les données bancaires ?",
    "Comment respecter le RGPD dans le KYC ?",
    "Quelles données financières sont obligatoires ?",
  ],
  commerce: [
    "Comment gérer le consentement cookies ?",
    "Quelle durée pour les données clients ?",
    "Comment traiter les données de paiement ?",
  ],
  education: [
    "Comment traiter les données d'élèves mineurs ?",
    "Quelles données scolaires peut-on conserver ?",
    "Comment informer les parents ?",
  ],
  juridique: [
    "Comment gérer la confidentialité des données clients ?",
    "Quelle base légale pour les données judiciaires ?",
  ],
  industrie: [
    "Comment gérer les données de vidéosurveillance ?",
    "Quelle durée pour les données d'accès ?",
  ],
};

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Bonjour ! Je suis votre assistant RGPD. Sélectionnez votre domaine d\'activité pour des réponses adaptées, puis posez vos questions.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [domaine, setDomaine] = useState('general');
  const [showHistorique, setShowHistorique] = useState(false);
  const [historique, setHistorique] = useState([]);
  const [loadingHistorique, setLoadingHistorique] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistorique = async () => {
    if (showHistorique) {
      setShowHistorique(false);
      return;
    }
    setLoadingHistorique(true);
    try {
      const response = await rgpdService.getHistorique();
      setHistorique(response.data);
      setShowHistorique(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistorique(false);
    }
  };

  const sendMessage = async (questionText = null) => {
    const question = questionText || input.trim();
    if (!question || loading) return;

    setInput('');
    const newMessages = [...messages, { role: 'user', content: question }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await rgpdService.chat(
        question,
        newMessages.slice(-6),
        domaine
      );
      const { answer, sources } = response.data;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: answer,
        sources: sources
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Erreur de communication avec l\'agent.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const suggestions = SUGGESTIONS[domaine] || SUGGESTIONS.general;

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <Navbar />
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col p-4 gap-4">

        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bot className="w-7 h-7 text-blue-400" />
            Agent RGPD
          </h1>
          <button
            onClick={loadHistorique}
            className="flex items-center gap-2 px-3 py-2 bg-gray-800
                       hover:bg-gray-700 text-gray-300 rounded-xl text-sm
                       border border-gray-700 transition-colors"
          >
            <History className="w-4 h-4" />
            Historique
            {showHistorique
              ? <ChevronUp className="w-4 h-4" />
              : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Historique déroulant */}
        {showHistorique && (
          <div className="bg-gray-800 rounded-xl border border-gray-700
                          max-h-64 overflow-y-auto p-4">
            <h3 className="text-white font-semibold mb-3 text-sm">
              Conversations précédentes
            </h3>
            {historique.length === 0 ? (
              <p className="text-gray-400 text-sm">Aucun historique</p>
            ) : (
              <div className="space-y-3">
                {historique.map((h) => (
                  <div key={h.id}
                    className="border-b border-gray-700 pb-3 cursor-pointer
                               hover:bg-gray-750 rounded p-2"
                    onClick={() => {
                      setMessages([
                        { role: 'user', content: h.question },
                        { role: 'assistant', content: h.answer,
                          sources: h.sources }
                      ]);
                      setShowHistorique(false);
                    }}
                  >
                    <p className="text-blue-400 text-sm font-medium truncate">
                      {h.question}
                    </p>
                    <p className="text-gray-400 text-xs mt-1 truncate">
                      {h.answer.substring(0, 100)}...
                    </p>
                    <p className="text-gray-600 text-xs mt-1">
                      {new Date(h.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Sélecteur de domaine */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
          <p className="text-gray-400 text-sm mb-3">
            Sélectionnez votre domaine pour des réponses adaptées :
          </p>
          <div className="flex flex-wrap gap-2">
            {DOMAINES.map((d) => (
              <button
                key={d.value}
                onClick={() => setDomaine(d.value)}
                className={`px-3 py-2 rounded-lg text-sm font-medium
                            transition-colors ${
                  domaine === d.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title={d.desc}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Suggestions */}
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => sendMessage(s)}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700
                         text-gray-300 text-xs rounded-lg border border-gray-700
                         transition-colors text-left"
            >
              {s}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-80">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 bg-blue-600 rounded-full flex
                                items-center justify-center shrink-0 mt-1">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
              <div className={`max-w-2xl rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-gray-800 text-gray-100 rounded-bl-sm border border-gray-700'
              }`}>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content}
                </p>
                {msg.sources?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-600">
                    <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Sources :
                    </p>
                    {msg.sources.map((src, j) => (
                      <span key={j}
                        className="inline-block text-xs bg-gray-700
                                   text-blue-300 rounded px-2 py-1 mr-1 mt-1">
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 bg-gray-600 rounded-full flex
                                items-center justify-center shrink-0 mt-1">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex
                              items-center justify-center shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3
                              border border-gray-700 flex items-center gap-2">
                <Loader className="w-5 h-5 text-blue-400 animate-spin" />
                <span className="text-gray-400 text-sm">
                  L'agent analyse votre question...
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Posez votre question RGPD ${
              domaine !== 'general'
                ? `(domaine: ${DOMAINES.find(d => d.value === domaine)?.label})`
                : ''
            }...`}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700
                       rounded-xl text-white placeholder-gray-400
                       focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-700
                       disabled:bg-gray-700 rounded-xl transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </form>
      </div>
    </div>
  );
}