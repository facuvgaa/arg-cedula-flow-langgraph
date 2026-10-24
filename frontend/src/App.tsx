import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Upload, 
  Car, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  Loader2
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  isStreaming?: boolean;
}

function StreamingMarkdownMessage({
  content,
  isStreaming = false,
  onStreamComplete,
  onStreamTick,
}: {
  content: string;
  isStreaming?: boolean;
  onStreamComplete?: () => void;
  onStreamTick?: () => void;
}) {
  const [displayedContent, setDisplayedContent] = useState(isStreaming ? '' : content);
  const [isTyping, setIsTyping] = useState(isStreaming);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayedContent(content);
      setIsTyping(false);
      return;
    }

    let currentIndex = 0;
    const totalLength = content.length;
    // Adaptación dinámica de velocidad: completa entre 1.0s y 2.0s según el largo
    const chunkSize = Math.max(1, Math.ceil(totalLength / 60));
    const intervalTime = 16;

    const interval = setInterval(() => {
      currentIndex = Math.min(currentIndex + chunkSize, totalLength);
      setDisplayedContent(content.slice(0, currentIndex));
      if (onStreamTick) onStreamTick();

      if (currentIndex >= totalLength) {
        clearInterval(interval);
        setIsTyping(false);
        if (onStreamComplete) onStreamComplete();
      }
    }, intervalTime);

    return () => clearInterval(interval);
  }, [content, isStreaming]);

  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
          strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
          em: ({ children }) => <em className="italic text-neutral-300">{children}</em>,
          ul: ({ children }) => <ul className="list-disc ml-5 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal ml-5 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          code: ({ children }) => (
            <code className="bg-neutral-800/90 text-sky-300 px-1.5 py-0.5 rounded font-mono text-xs border border-neutral-700/50">
              {children}
            </code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-sky-500 pl-3 my-2 italic text-neutral-400">
              {children}
            </blockquote>
          ),
          h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2 mt-1">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-bold text-white mb-1.5 mt-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-bold text-sky-400 mb-1 mt-1">{children}</h3>,
        }}
      >
        {displayedContent}
      </ReactMarkdown>
      {isTyping && (
        <span className="inline-block w-1.5 h-4 ml-1 bg-sky-400 animate-pulse align-middle" />
      )}
    </div>
  );
}

interface VehicleData {
  dominio?: string;
  marca?: string;
  modelo?: string;
  year?: number;
  tipo?: string;
  uso?: string;
  chasis?: string;
  motor?: string;
}

interface OwnerData {
  nombre_completo?: string;
  documento?: string;
  domicilio?: string;
  codigo_postal?: string;
}

interface QuoteCoverages {
  RESPONSABILIDAD_CIVIL?: number;
  TERCEROS_COMPLETO?: number;
  TODO_RIESGO?: number;
}

interface QuoteResult {
  vehicleDescription?: string;
  vehicleMarketValue?: number;
  postalCode?: string;
  coverages?: QuoteCoverages;
}

interface PolicyResult {
  policyNumber?: string;
  customerName?: string;
  customerEmail?: string;
  brand?: string;
  model?: string;
  coverageType?: string;
  monthlyPremium?: number;
  status?: string;
}

const API_BASE = "http://localhost:8001";

export default function App() {
  const [sessionId] = useState<string>(() => {
    const saved = sessionStorage.getItem("seguros_session_id");
    if (saved) return saved;
    const newId = crypto.randomUUID();
    sessionStorage.setItem("seguros_session_id", newId);
    return newId;
  });

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '¡Hola! Soy tu asistente de seguros de La Caja. Podés subir la foto de tu cédula verde o azul para extraer los datos de tu vehículo y cotizar al instante con AWS Bedrock AI.',
      source: 'AWS Bedrock Vision OCR & Asistente La Caja'
    }
  ]);

  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [vehicleData, setVehicleData] = useState<VehicleData | null>(null);
  const [ownerData, setOwnerData] = useState<OwnerData | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [postalCode, setPostalCode] = useState<string | null>(null);
  const [quoteResult, setQuoteResult] = useState<QuoteResult | null>(null);
  const [selectedCoverage, setSelectedCoverage] = useState<string>('');
  const [policyResult, setPolicyResult] = useState<PolicyResult | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<string>('IDLE');

  // Manual inputs for slot-filling if needed
  const [inputYear, setInputYear] = useState<string>('');
  const [inputCp, setInputCp] = useState<string>('');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleApiResponse = (data: any) => {
    if (data.vehicle_data) setVehicleData(data.vehicle_data);
    if (data.owner_data) setOwnerData(data.owner_data);
    if (data.year) {
      setYear(data.year);
      setInputYear(String(data.year));
    }
    if (data.postal_code) {
      setPostalCode(data.postal_code);
      setInputCp(data.postal_code);
    }
    if (data.quote_result) {
      setQuoteResult(data.quote_result);
      if (!selectedCoverage) setSelectedCoverage('TERCEROS_COMPLETO');
    }
    if (data.selected_coverage) setSelectedCoverage(data.selected_coverage);
    if (data.policy_result) setPolicyResult(data.policy_result);
    if (data.status) setWorkflowStatus(data.status);

    if (data.message) {
      let source = "AWS Bedrock AI Asesor";
      if (data.status === "QUOTES_AVAILABLE") source = "Servidor MCP & Motor Tarifario";
      else if (data.status === "POLICY_ISSUED") source = "Servidor MCP - Emisión de Póliza";
      else if (data.quote_result) source = "RAG La Caja - Póliza Oficial";
      else if (data.vehicle_data) source = `AWS Bedrock Vision OCR - Cédula N° ${data.vehicle_data.dominio || ''}`;

      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.message,
          source,
          isStreaming: true,
        }
      ]);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text
    };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('user_message', text);
      if (year) formData.append('year', String(year));
      if (postalCode) formData.append('postal_code', postalCode);

      const res = await fetch(`${API_BASE}/v1/vehicle-cards/process`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Error en el servidor' }));
        throw new Error(errData.detail || 'Error en la solicitud');
      }

      const data = await res.json();
      handleApiResponse(data);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⚠️ Hubo un error de conexión: ${err.message || 'Verificá que el backend esté ejecutándose en el puerto 8001.'}`,
          source: 'Error del Sistema'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setMessages(prev => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: 'user',
        content: `📄 Subiste el archivo: ${file.name}`
      },
      {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Escaneando cédula "${file.name}" con AWS Bedrock Vision...`,
        source: 'AWS Bedrock Vision OCR Engine'
      }
    ]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      if (inputYear) formData.append('year', inputYear);
      if (inputCp) formData.append('postal_code', inputCp);

      const res = await fetch(`${API_BASE}/v1/vehicle-cards/process`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Error procesando la cédula' }));
        throw new Error(errData.detail || 'Error procesando la cédula');
      }

      const data = await res.json();
      handleApiResponse(data);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `❌ No se pudo procesar la cédula: ${err.message}`,
          source: 'Error OCR'
        }
      ]);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleManualDataSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputYear && !inputCp) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      if (inputYear) formData.append('year', inputYear);
      if (inputCp) formData.append('postal_code', inputCp);

      const res = await fetch(`${API_BASE}/v1/vehicle-cards/process`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Error actualizando datos' }));
        throw new Error(errData.detail);
      }

      const data = await res.json();
      handleApiResponse(data);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⚠️ Error al guardar año y CP: ${err.message}`,
          source: 'Error del Sistema'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectCoverage = (covKey: string, covName: string) => {
    setSelectedCoverage(covKey);
    handleSendMessage(`Quiero seleccionar la cobertura ${covName}`);
  };



  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return '—';
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const isMissingYearOrCp = (workflowStatus.includes('WAITING_YEAR') || workflowStatus.includes('WAITING_CP')) && (!year || !postalCode);

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-neutral-800/80 bg-[#0e1420]/90 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Cotizador y Asistente IA
            </h1>
            <p className="text-xs md:text-sm text-neutral-400 mt-0.5">
              La Caja Seguros - Asistencia e Inteligencia Documental
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-700/60 text-emerald-400 text-xs font-medium shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              AWS Bedrock Conectado
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Chat Assistant */}
        <section className="lg:col-span-7 flex flex-col h-[calc(100vh-140px)] min-h-[580px] bg-[#111722]/80 border border-neutral-800/80 rounded-2xl shadow-xl overflow-hidden">
          
          {/* Chat Messages Scroll Area */}
          <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md ${
                    msg.role === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none'
                      : 'bg-[#171f2d] border border-neutral-800 text-neutral-200 rounded-bl-none'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <StreamingMarkdownMessage
                      content={msg.content}
                      isStreaming={msg.isStreaming}
                      onStreamTick={scrollToBottom}
                      onStreamComplete={() => {
                        setMessages((prev) =>
                          prev.map((m) => (m.id === msg.id ? { ...m, isStreaming: false } : m))
                        );
                      }}
                    />
                  )}
                </div>
                {msg.source && (
                  <span className="text-[11px] text-neutral-500 italic mt-1.5 px-1 font-mono">
                    Fuente: {msg.source}
                  </span>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-sky-400 bg-sky-950/30 border border-sky-900/40 rounded-xl px-4 py-2.5 w-fit animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                <span>AWS Bedrock y Spring Boot MCP procesando tu consulta...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Policy Issued Banner if Complete */}
          {policyResult && (
            <div className="mx-4 mb-2 p-3 bg-emerald-950/70 border border-emerald-600/70 rounded-xl flex items-center justify-between text-xs text-emerald-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-semibold block">Póliza Emitida: {policyResult.policyNumber || 'POL-EXITOSA'}</span>
                  <span>Constancia enviada a {policyResult.customerEmail || 'tu email'}.</span>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-300 font-bold rounded-lg border border-emerald-500/30">
                ACTIVA
              </span>
            </div>
          )}

          {/* Quick Action Chips */}
          <div className="px-4 py-2 border-t border-neutral-800/60 bg-[#0e1420]/60 flex items-center gap-2 overflow-x-auto no-scrollbar">
            <button
              type="button"
              onClick={() => handleSendMessage('¿Cuántos kilómetros de grúa incluye mi póliza?')}
              className="whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-medium bg-[#171f2d] hover:bg-neutral-800 border border-neutral-700/80 text-neutral-300 transition-colors"
            >
              ¿Km de grúa?
            </button>
            <button
              type="button"
              onClick={() => handleSendMessage('¿Qué cubre el plan Terceros Completo con granizo?')}
              className="whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-medium bg-[#171f2d] hover:bg-neutral-800 border border-neutral-700/80 text-neutral-300 transition-colors"
            >
              ¿Cobertura Terceros?
            </button>
            <button
              type="button"
              onClick={() => handleSendMessage('¿Cubre rotura de cerraduras, cristales o inundación?')}
              className="whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-medium bg-[#171f2d] hover:bg-neutral-800 border border-neutral-700/80 text-neutral-300 transition-colors"
            >
              ¿Cubre granizo?
            </button>
            <button
              type="button"
              onClick={() => handleSendMessage(`Quiero emitir la póliza de ${selectedCoverage}`)}
              className="whitespace-nowrap px-3.5 py-1.5 rounded-full text-xs font-semibold bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-300 transition-colors"
            >
              Emitir Póliza
            </button>
          </div>

          {/* Chat Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-3 md:p-4 border-t border-neutral-800 bg-[#111722] flex items-center gap-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Escriba su consulta o email para emitir..."
              disabled={isLoading}
              className="flex-1 bg-[#171f2d] border border-neutral-700/80 rounded-full px-5 py-2.5 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-sky-500 transition-colors disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="bg-sky-400 hover:bg-sky-300 disabled:opacity-40 disabled:hover:bg-sky-400 text-neutral-950 font-semibold px-5 py-2.5 rounded-full text-sm flex items-center gap-1.5 transition-all shadow-md active:scale-95"
            >
              <span>Enviar</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </section>

        {/* Right Column: Vehicle Card + Compact Policies */}
        <section className="lg:col-span-5 flex flex-col gap-5">
          
          {/* Top Card: Datos del Vehículo */}
          <div className="bg-[#111722]/80 border border-neutral-800/80 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Car className="w-4 h-4 text-sky-400" />
                Datos del Vehículo
              </h2>
              <span className="bg-sky-950/80 border border-sky-800/80 text-sky-400 text-xs px-2.5 py-0.5 rounded-full font-medium">
                AWS Bedrock OCR
              </span>
            </div>

            {/* 2x2 Grid of vehicle details */}
            <div className="grid grid-cols-2 gap-3.5 mt-4">
              <div className="bg-[#171f2d]/60 border border-neutral-800/60 rounded-xl p-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                  DOMINIO
                </span>
                <span className="text-sm md:text-base font-bold text-white mt-0.5 block truncate">
                  {vehicleData?.dominio || '—'}
                </span>
              </div>

              <div className="bg-[#171f2d]/60 border border-neutral-800/60 rounded-xl p-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                  TITULAR
                </span>
                <span className="text-sm md:text-base font-bold text-white mt-0.5 block truncate">
                  {ownerData?.nombre_completo || '—'}
                </span>
              </div>

              <div className="bg-[#171f2d]/60 border border-neutral-800/60 rounded-xl p-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                  VEHÍCULO
                </span>
                <span className="text-sm md:text-base font-bold text-white mt-0.5 block truncate">
                  {vehicleData?.marca && vehicleData?.modelo
                    ? `${vehicleData.marca} ${vehicleData.modelo}`
                    : '—'}
                </span>
              </div>

              <div className="bg-[#171f2d]/60 border border-neutral-800/60 rounded-xl p-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                  AÑO / CP
                </span>
                <span className="text-sm md:text-base font-bold text-white mt-0.5 block truncate">
                  {(year || vehicleData?.year) ? (year || vehicleData?.year) : '—'} - CP {(postalCode || ownerData?.codigo_postal) ? (postalCode || ownerData?.codigo_postal) : '—'}
                </span>
              </div>
            </div>

            {/* Suma Asegurada Row */}
            <div className="mt-3.5 bg-[#171f2d]/90 border border-neutral-800 rounded-xl p-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                SUMA ASEGURADA
              </span>
              <span className="text-lg md:text-xl font-bold text-sky-400">
                {quoteResult?.vehicleMarketValue 
                  ? formatCurrency(quoteResult.vehicleMarketValue) 
                  : '—'}
              </span>
            </div>

            {/* Missing Data Slot Filling Form (If required) */}
            {isMissingYearOrCp && (
              <form onSubmit={handleManualDataSubmit} className="mt-4 p-3 bg-amber-950/40 border border-amber-600/60 rounded-xl">
                <div className="flex items-center gap-1.5 text-xs text-amber-300 font-medium mb-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Completar datos faltantes para cotizar:</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-neutral-400 block mb-1">Año de fabricación</label>
                    <input
                      type="number"
                      placeholder="Ej: 2022"
                      value={inputYear}
                      onChange={(e) => setInputYear(e.target.value)}
                      className="w-full bg-[#111722] border border-neutral-700 rounded-lg px-2.5 py-1.5 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-neutral-400 block mb-1">Código Postal</label>
                    <input
                      type="text"
                      placeholder="Ej: 1636"
                      value={inputCp}
                      onChange={(e) => setInputCp(e.target.value)}
                      className="w-full bg-[#111722] border border-neutral-700 rounded-lg px-2.5 py-1.5 text-xs text-white"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="mt-2.5 w-full bg-amber-500 hover:bg-amber-400 text-neutral-950 font-semibold py-1.5 rounded-lg text-xs transition-colors"
                >
                  Confirmar y Cotizar
                </button>
              </form>
            )}

            {/* Upload Action Area */}
            <div className="mt-4 border border-dashed border-neutral-700/80 rounded-xl p-3 flex items-center justify-center bg-[#171f2d]/30">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,application/pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold text-neutral-100 bg-[#171f2d] hover:bg-neutral-800 border border-neutral-700 hover:border-neutral-600 transition-all shadow-sm active:scale-[0.99]"
              >
                <Upload className="w-4 h-4 text-sky-400" />
                <span>Subir Cédula Verde/Azul</span>
              </button>
            </div>
          </div>

          {/* Bottom Card: Compact Policies Panel (appears after quoting) */}
          {quoteResult?.coverages ? (
            <div className="bg-[#111722]/80 border border-neutral-800/80 rounded-2xl p-4 shadow-xl">
              <div className="flex items-center justify-between pb-2.5 border-b border-neutral-800">
                <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-sky-400" />
                  Pólizas Disponibles
                </h3>
                <span className="text-[11px] text-neutral-400 italic">
                  Cotización mensual
                </span>
              </div>

              {/* Compact Policy Items List */}
              <div className="mt-3 space-y-2">
                
                {/* Plan 1: Responsabilidad Civil */}
                {quoteResult.coverages.RESPONSABILIDAD_CIVIL && (
                  <div
                    onClick={() => handleSelectCoverage('RESPONSABILIDAD_CIVIL', 'Responsabilidad Civil')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedCoverage === 'RESPONSABILIDAD_CIVIL'
                        ? 'border-sky-500 bg-sky-950/20 shadow-md shadow-sky-950/50 ring-1 ring-sky-500/50'
                        : 'border-neutral-800/80 bg-[#171f2d]/50 hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 pr-2">
                        <span className="font-semibold text-xs text-white block">
                          Responsabilidad Civil
                        </span>
                        <p className="text-[11px] text-neutral-400 mt-0.5 line-clamp-1">
                          Cobertura básica obligatoria ante daños a terceros.
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-sm font-bold text-sky-400 block">
                          {formatCurrency(quoteResult.coverages.RESPONSABILIDAD_CIVIL)}
                        </span>
                        <span className="text-[10px] text-neutral-500">/mes</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Plan 2: Terceros Completo */}
                {quoteResult.coverages.TERCEROS_COMPLETO && (
                  <div
                    onClick={() => handleSelectCoverage('TERCEROS_COMPLETO', 'Terceros Completo')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedCoverage === 'TERCEROS_COMPLETO'
                        ? 'border-sky-500 bg-sky-950/20 shadow-md shadow-sky-950/50 ring-1 ring-sky-500/50'
                        : 'border-neutral-800/80 bg-[#171f2d]/50 hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 pr-2">
                        <div className="flex items-center gap-1.5">
                          <span className="font-semibold text-xs text-white block">
                            Terceros Completo
                          </span>
                          <span className="bg-sky-500/20 text-sky-300 text-[9px] px-1.5 py-0.2 rounded font-medium border border-sky-500/30">
                            RECOMENDADO
                          </span>
                        </div>
                        <p className="text-[11px] text-neutral-400 mt-0.5 line-clamp-1">
                          Robo, incendio total/parcial, cristales y granizo.
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-sm font-bold text-sky-400 block">
                          {formatCurrency(quoteResult.coverages.TERCEROS_COMPLETO)}
                        </span>
                        <span className="text-[10px] text-neutral-500">/mes</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Plan 3: Todo Riesgo */}
                {quoteResult.coverages.TODO_RIESGO && (
                  <div
                    onClick={() => handleSelectCoverage('TODO_RIESGO', 'Todo Riesgo con Franquicia')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedCoverage === 'TODO_RIESGO'
                        ? 'border-sky-500 bg-sky-950/20 shadow-md shadow-sky-950/50 ring-1 ring-sky-500/50'
                        : 'border-neutral-800/80 bg-[#171f2d]/50 hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 pr-2">
                        <span className="font-semibold text-xs text-white block">
                          Todo Riesgo con Franquicia
                        </span>
                        <p className="text-[11px] text-neutral-400 mt-0.5 line-clamp-1">
                          Máxima protección con franquicia fija ante cualquier siniestro.
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-sm font-bold text-sky-400 block">
                          {formatCurrency(quoteResult.coverages.TODO_RIESGO)}
                        </span>
                        <span className="text-[10px] text-neutral-500">/mes</span>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </div>
          ) : (
            <div className="bg-[#111722]/50 border border-neutral-800/60 rounded-2xl p-5 text-center shadow-lg">
              <ShieldCheck className="w-7 h-7 text-neutral-600 mx-auto mb-2" />
              <p className="text-xs text-neutral-300 font-semibold">Pólizas y Cotización Mensual</p>
              <p className="text-[11px] text-neutral-500 mt-1 max-w-xs mx-auto">
                Las opciones de cobertura se calcularán automáticamente por el motor tarifario cuando se procese la cédula.
              </p>
            </div>
          )}

        </section>
      </main>
    </div>
  );
}
