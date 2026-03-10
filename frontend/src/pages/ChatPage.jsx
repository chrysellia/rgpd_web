import { useState, useRef, useEffect } from 'react';
import { rgpdService } from '../services/api';
import Navbar from '../components/Navbar';
import { Send, Bot, User, FileText, Loader } from 'lucide-react';

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Bonjour ! Je suis votre assistant RGPD. Posez-moi vos questions sur la conformité, les traitements de données, ou les obligations réglementaires.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const response = await rgpdService.chat(question);
      const { answer, sources } = response.data;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: answer,
        sources: sources
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Erreur lors de la communication avec l\'agent. Vérifiez que le backend est actif.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <Navbar />
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col p-4">

        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
          <Bot className="w-7 h-7 text-blue-400" />
          Agent RGPD
        </h1>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-96">
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

                {/* Sources */}
                {msg.sources?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-600">
                    <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Sources utilisées :
                    </p>
                    {msg.sources.map((src, j) => (
                      <span key={j} className="inline-block text-xs bg-gray-700
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
                              border border-gray-700">
                <Loader className="w-5 h-5 text-blue-400 animate-spin" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question RGPD..."
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