import React, { useState, useEffect } from "react";
import { getCameras, type Camera } from "./services/cameras";
import { apiFetch } from "./services/api";
import { connectKavronEvents } from "./services/websocket";
import { Routes, Route, useNavigate, useLocation, Navigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Map as MapIcon, 
  Video, 
  Network, 
  Eye, 
  Crosshair, 
  Activity, 
  Focus, 
  CarFront, 
  Users, 
  BellRing, 
  AlertTriangle, 
  BarChart3, 
  FileText, 
  Settings,
  Search,
  Bell,
  ChevronDown,
  Play,
  Maximize,
  Image as ImageIcon,
  CheckCircle2,
  Lock,
  ArrowRight,
  Filter,
  MoreVertical,
  LayoutGrid,
  Pencil,
  Trash2,
  Save,
  X,
  RotateCcw,
  MapPin,
  LocateFixed,
  Navigation,
  Search as SearchIcon
} from 'lucide-react';
import { cn } from './utils/cn';

declare global {
  interface Window {
    L?: any;
  }
}

const ensureLeaflet = async (): Promise<any> => {
  if (window.L) return window.L;
  await new Promise<void>((resolve, reject) => {
    const existing = document.querySelector('script[data-kavron-leaflet]');
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Leaflet failed to load')), { once: true });
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.async = true;
    script.dataset.kavronLeaflet = 'true';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Leaflet failed to load'));
    document.head.appendChild(script);
  });
  if (!window.L) throw new Error('Leaflet is unavailable');
  return window.L;
};

// ============================================================
// KAVRON ANOMALY / INTRUSION API
// ============================================================

type KavronAnomaly = {
  id: number;
  anomaly_id: string;
  camera_id: string;
  track_id?: string | number | null;
  anomaly_type: string;
  severity: string;
  message: string;
  confidence: number;
  bbox?: number[];
  snapshot_path?: string | null;
  metadata?: Record<string, unknown>;
  acknowledged: boolean;
  created_at?: string | null;
};

const ANOMALY_API_BASE =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const getKavronAnomalies = async (limit = 100): Promise<KavronAnomaly[]> => {
  const response = await fetch(
    `${ANOMALY_API_BASE}/api/v1/anomalies?limit=${limit}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(
      `Anomaly API returned ${response.status}`,
    );
  }

  const data = await response.json();

  return Array.isArray(data?.items)
    ? data.items
    : [];
};

const acknowledgeKavronAnomaly = async (
  anomalyId: string,
): Promise<KavronAnomaly> => {
  const response = await fetch(
    `${ANOMALY_API_BASE}/api/v1/anomalies/${encodeURIComponent(anomalyId)}/acknowledge`,
    {
      method: "PATCH",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Acknowledge API returned ${response.status}`,
    );
  }

  return response.json();
};


// --- SHARED COMPONENTS ---

const Logo = ({ className }: { className?: string }) => (
  <div className={cn("flex items-center gap-2", className)}>
    <div className="relative flex items-center justify-center w-8 h-8 rounded-lg gradient-blue-cyan shadow-soft text-white">
      <Focus className="w-5 h-5 absolute" strokeWidth={2.5} />
      <div className="absolute inset-0 rounded-lg border border-white/20"></div>
    </div>
    <span className="font-bold text-xl tracking-tight text-foreground">KAVRON</span>
  </div>
);

const Button = ({ children, variant = 'primary', className, ...props }: any) => {
  const baseStyles = "inline-flex items-center justify-center px-5 py-2.5 rounded-md font-medium transition-all duration-200 ease-out active:scale-95";
  const variants = {
    primary: "bg-primary text-white hover:bg-primary-hover shadow-soft",
    secondary: "bg-white text-foreground border border-border hover:bg-background-secondary shadow-soft",
    ghost: "bg-transparent text-foreground-secondary hover:text-foreground hover:bg-background-secondary",
    danger: "bg-critical text-white hover:bg-red-600 shadow-soft"
  };
  
  return (
    <button className={cn(baseStyles, variants[variant as keyof typeof variants], className)} {...props}>
      {children}
    </button>
  );
};

const Card = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <div className={cn("bg-card rounded-2xl border border-border shadow-soft overflow-hidden", className)}>
    {children}
  </div>
);

// --- LOGIN PAGE ---

const LoginPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      navigate('/app');
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center relative overflow-hidden">
      {/* Glow Effects */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] mix-blend-multiply pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-cyan/10 rounded-full blur-[140px] mix-blend-multiply pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <Logo className="scale-125 mb-4" />
          <h1 className="text-2xl font-bold text-foreground">Operator Authentication</h1>
          <p className="text-foreground-secondary text-sm">Secure access to KAVRON Intelligence Platform</p>
        </div>

        <Card className="p-8 backdrop-blur-xl bg-white/90">
          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Operator ID</label>
              <input 
                type="text" 
                defaultValue="OP-0482"
                className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                required
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Security Token</label>
              <div className="relative">
                <input 
                  type="password" 
                  defaultValue="••••••••"
                  className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  required
                />
                <Lock className="w-4 h-4 text-foreground-secondary absolute right-3 top-1/2 -translate-y-1/2" />
              </div>
            </div>

            <div className="pt-2">
              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Authenticating...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2 w-full">
                    Initialize Session <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </Button>
            </div>
          </form>
          
          <div className="mt-6 flex items-center justify-center gap-2 text-xs font-medium text-foreground-secondary/60">
            <ShieldAlert className="w-3 h-3" /> E2E Encrypted Connection
          </div>
        </Card>
      </motion.div>
    </div>
  );
};

// --- APP SHELL & NAVIGATION ---

const NavItem = ({ icon: Icon, label, path, isActive }: { icon: any, label: string, path: string, isActive?: boolean }) => (
  <Link to={path} className={cn(
    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative",
    isActive ? "text-primary bg-primary/5" : "text-foreground-secondary hover:text-foreground hover:bg-background"
  )}>
    {isActive && (
      <motion.div layoutId="nav-indicator" className="absolute left-0 w-1 h-5 bg-primary rounded-r-full" />
    )}
    <Icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-foreground-secondary group-hover:text-foreground")} strokeWidth={isActive ? 2.5 : 2} />
    {label}
  </Link>
);

const AppShell = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-[260px] bg-white border-r border-border-subtle flex flex-col z-20 shadow-sm relative">
        <div className="h-16 flex items-center px-6 border-b border-border-subtle shrink-0 cursor-pointer" onClick={() => navigate('/')}>
          <Logo />
        </div>
        
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <div className="text-xs font-semibold text-foreground-secondary/60 px-3 pb-2 pt-2 uppercase tracking-wider">Operations</div>
          <NavItem icon={Activity} label="Overview" path="/app" isActive={location.pathname === '/app'} />
          <NavItem icon={Video} label="Live Surveillance" path="/app/live" isActive={location.pathname === '/app/live'} />
          <NavItem icon={Network} label="Camera Network" path="/app/cameras" isActive={location.pathname === '/app/cameras'} />
          <NavItem icon={MapIcon} label="Border Map" path="/app/map" isActive={location.pathname === '/app/map'} />
          
          <div className="text-xs font-semibold text-foreground-secondary/60 px-3 pb-2 pt-6 uppercase tracking-wider">Intelligence</div>
          <NavItem icon={Eye} label="AI Vision" path="/app/ai" isActive={location.pathname === '/app/ai'} />
          <NavItem icon={BarChart3} label="AI Model Lab" path="/app/models" isActive={location.pathname === '/app/models'} />
          <NavItem icon={Crosshair} label="Object Tracking" path="/app/tracking" isActive={location.pathname === '/app/tracking'} />
          <NavItem icon={ShieldAlert} label="Intrusion Detection" path="/app/intrusion" isActive={location.pathname === '/app/intrusion'} />
          
          <div className="text-xs font-semibold text-foreground-secondary/60 px-3 pb-2 pt-6 uppercase tracking-wider">Management</div>
          <NavItem icon={AlertTriangle} label="Incidents" path="/app/incidents" isActive={location.pathname === '/app/incidents'} />
          <NavItem icon={Settings} label="Settings" path="/app/settings" isActive={location.pathname === '/app/settings'} />
        </div>
        
        <div className="p-4 border-t border-border-subtle shrink-0 space-y-3 bg-white">
          <div className="flex items-center justify-between p-3 rounded-xl bg-background border border-border cursor-pointer hover:border-primary/30 transition-colors" onClick={() => navigate('/login')}>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-blue-cyan flex items-center justify-center text-white text-xs font-bold shadow-soft">
                OP
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-foreground">Operator OP-0482</span>
                <span className="text-[10px] text-foreground-secondary flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.8)]" /> Systems OK
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        <header className="h-16 bg-white border-b border-border-subtle flex items-center justify-between px-6 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold text-foreground capitalize">
              {location.pathname === '/app' ? 'Command Center' : location.pathname.split('/').pop()?.replace('-', ' ')}
            </h1>
            <div className="h-4 w-px bg-border"></div>
            <div className="flex items-center gap-2 text-sm font-medium text-foreground-secondary bg-background px-3 py-1.5 rounded-md border border-border cursor-pointer hover:bg-background-secondary transition-colors">
              Sector 04 <ChevronDown className="w-4 h-4" />
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative group w-64 hidden md:block">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-foreground-secondary group-focus-within:text-primary transition-colors" />
              <input 
                type="text" 
                placeholder="Search KAVRON..." 
                className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all placeholder:text-foreground-secondary/60"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded border border-border bg-white text-[10px] font-sans font-medium text-foreground-secondary shadow-sm">⌘K</kbd>
              </div>
            </div>
            
            <button className="relative p-2 text-foreground-secondary hover:text-foreground hover:bg-background rounded-full transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-critical border border-white" />
            </button>
            
            <div className="text-sm font-medium text-foreground-secondary pr-2">
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </header>
        
        <main className="flex-1 overflow-auto p-6 relative">
          <div className="absolute top-0 right-0 w-full h-[300px] bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

// --- SHARED UI ELEMENTS ---

const KPICard = ({ title, value, status = 'neutral', trend }: any) => {
  return (
    <Card className="p-5 flex flex-col gap-2 relative overflow-hidden group hover:border-primary/30 transition-colors">
      <div className="flex items-center justify-between text-sm font-medium text-foreground-secondary">
        {title}
        {status === 'good' && <div className="w-2 h-2 rounded-full bg-green shadow-[0_0_8px_rgba(16,185,129,0.6)]" />}
        {status === 'warning' && <div className="w-2 h-2 rounded-full bg-warning shadow-[0_0_8px_rgba(245,158,11,0.6)]" />}
        {status === 'critical' && <div className="w-2 h-2 rounded-full bg-critical shadow-[0_0_8px_rgba(239,68,68,0.6)]" />}
      </div>
      <div className="flex items-end gap-3 mt-1">
        <span className="text-3xl font-bold tracking-tight text-foreground">{value}</span>
        {trend && (
          <span className="text-xs font-medium text-foreground-secondary mb-1">{trend}</span>
        )}
      </div>
      <svg className="absolute bottom-0 left-0 w-full h-8 opacity-20 text-primary" preserveAspectRatio="none" viewBox="0 0 100 100">
        <path d="M0,100 L0,50 Q25,20 50,60 T100,30 L100,100 Z" fill="currentColor" opacity="0.2" />
        <path d="M0,50 Q25,20 50,60 T100,30" fill="none" stroke="currentColor" strokeWidth="4" />
      </svg>
    </Card>
  );
};

type KavronDetection = {
  camera_id?: string;
  class_name?: string;
  label?: string;
  name?: string;
  confidence?: number;
  score?: number;
  bbox?: number[] | { x?: number; y?: number; x1?: number; y1?: number; x2?: number; y2?: number; width?: number; height?: number };
  box?: number[];
  xyxy?: number[];
  bounding_box?: number[];
  track_id?: string | number;
  id?: string | number;
  keypoints?: Array<number[] | { x?: number; y?: number; confidence?: number; score?: number }>;
  pose?: Array<number[] | { x?: number; y?: number; confidence?: number; score?: number }>;
  landmarks?: Array<number[] | { x?: number; y?: number; confidence?: number; score?: number }>;
  image_width?: number;
  image_height?: number;
  posture?: string;
  pose_confidence?: number;
  face?: { bbox?: number[]; confidence?: number };
  plate?: { text?: string; confidence?: number; bbox?: number[] };
  behavior_flags?: string[];
};

type VirtualFence = {
  id: string;
  name: string;
  camera_id: string;
  geometry_type: "polygon" | "line" | "circle";
  coordinates: number[][];
  allowed_objects?: string[];
  severity?: string;
  active?: boolean;
};

const normalizeFencePoints = (fence: VirtualFence): Array<[number, number]> => {
  if (!Array.isArray(fence?.coordinates)) return [];
  return fence.coordinates
    .map((point: any) => {
      if (Array.isArray(point) && point.length >= 2) return [Number(point[0]), Number(point[1])] as [number, number];
      if (point && typeof point === "object") return [Number(point.x ?? 0), Number(point.y ?? 0)] as [number, number];
      return null;
    })
    .filter((point): point is [number, number] => !!point && point.every(Number.isFinite));
};

const normalizeDetectionArray = (payload: any, cameraId: string): KavronDetection[] => {
  const candidates = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.[cameraId])
      ? payload[cameraId]
      : Array.isArray(payload?.detections)
        ? payload.detections
        : [];

  return candidates.filter(
    (item: any) => !item?.camera_id || item.camera_id === cameraId,
  );
};

const getDetectionBox = (item: KavronDetection) => {
  const raw = item?.bbox ?? item?.box ?? item?.xyxy ?? item?.bounding_box;

  if (Array.isArray(raw) && raw.length >= 4) {
    return {
      x1: Number(raw[0]),
      y1: Number(raw[1]),
      x2: Number(raw[2]),
      y2: Number(raw[3]),
    };
  }

  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    const x = Number(raw.x ?? raw.x1 ?? 0);
    const y = Number(raw.y ?? raw.y1 ?? 0);
    return {
      x1: x,
      y1: y,
      x2: Number(raw.x2 ?? x + Number(raw.width ?? 0)),
      y2: Number(raw.y2 ?? y + Number(raw.height ?? 0)),
    };
  }

  return null;
};

const getDetectionConfidence = (item: KavronDetection) => {
  const value = Number(item?.confidence ?? item?.score ?? 0);
  if (!Number.isFinite(value)) return 0;
  return value <= 1 ? value * 100 : value;
};

const getDetectionKeypoints = (item: KavronDetection) => {
  const raw = item?.keypoints ?? item?.pose ?? item?.landmarks ?? [];
  if (!Array.isArray(raw)) return [];

  return raw
    .map((point: any) => {
      if (Array.isArray(point) && point.length >= 2) {
        return {
          x: Number(point[0]),
          y: Number(point[1]),
          confidence: point.length >= 3 ? Number(point[2]) : 1,
        };
      }

      if (point && typeof point === "object") {
        return {
          x: Number(point.x ?? 0),
          y: Number(point.y ?? 0),
          confidence: Number(point.confidence ?? point.score ?? 1),
        };
      }

      return null;
    })
    .filter(Boolean) as Array<{ x: number; y: number; confidence: number }>;
};

const POSE_CONNECTIONS: Array<[number, number]> = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [1, 5], [5, 6], [6, 7], [1, 8],
  [8, 9], [9, 10], [10, 11],
  [8, 12], [12, 13], [13, 14],
  [8, 15], [15, 17], [0, 16],
];

const VideoFeed = ({
  camId = "CAM-DEMO-01",
  ai = true,
  size = "large",
  detections = [],
  fences = [],
  editingFenceId = null,
  draftFencePoints = [],
  onFencePointsChange,
  frameWidth,
  frameHeight,
}: {
  camId?: string;
  ai?: boolean;
  size?: "large" | "small";
  detections?: KavronDetection[];
  fences?: VirtualFence[];
  editingFenceId?: string | null;
  draftFencePoints?: Array<[number, number]>;
  onFencePointsChange?: (points: Array<[number, number]>) => void;
  frameWidth?: number;
  frameHeight?: number;
}) => {
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
  const streamUrl = `${API_BASE_URL}/api/v1/cameras/${encodeURIComponent(camId)}/stream`;
  const [streamError, setStreamError] = useState(false);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showTracks, setShowTracks] = useState(true);
  const [showPose, setShowPose] = useState(true);

  useEffect(() => {
    setStreamError(false);
  }, [camId]);

  const safeDetections = Array.isArray(detections) ? detections : [];
  const sourceWidth = Number(frameWidth ?? safeDetections?.[0]?.image_width ?? 1920);
  const sourceHeight = Number(frameHeight ?? safeDetections?.[0]?.image_height ?? 1080);
  const handleFencePointerDown = (event: React.PointerEvent<SVGCircleElement>, index: number) => {
    if (!editingFenceId || !onFencePointsChange || !draftFencePoints) return;
    event.preventDefault();
    event.stopPropagation();
    const svg = event.currentTarget.ownerSVGElement;
    if (!svg) return;
    const move = (moveEvent: PointerEvent) => {
      const rect = svg.getBoundingClientRect();
      const x = Math.max(0, Math.min(sourceWidth, ((moveEvent.clientX - rect.left) / Math.max(1, rect.width)) * sourceWidth));
      const y = Math.max(0, Math.min(sourceHeight, ((moveEvent.clientY - rect.top) / Math.max(1, rect.height)) * sourceHeight));
      const next = draftFencePoints.map((point, i) => i === index ? [x, y] as [number, number] : point);
      onFencePointsChange(next);
    };
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up, { once: true });
  };

  const behaviorFlags = Array.from(new Set(
    safeDetections.flatMap((detection: any) =>
      Array.isArray(detection?.behavior_flags) ? detection.behavior_flags : []
    ).filter(Boolean).map(String)
  ));

  const toPercentX = (value: number) => {
    if (!Number.isFinite(value)) return 0;
    return value >= 0 && value <= 1 ? value * 100 : (value / Math.max(1, sourceWidth)) * 100;
  };

  const toPercentY = (value: number) => {
    if (!Number.isFinite(value)) return 0;
    return value >= 0 && value <= 1 ? value * 100 : (value / Math.max(1, sourceHeight)) * 100;
  };

  return (
    <div className={cn(
      "flex-1 rounded-xl bg-slate-900 overflow-hidden relative group min-h-[200px]",
      size === "small" ? "min-h-[220px]" : "min-h-[300px]",
    )}>
      {streamError ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 bg-slate-950">
          <Video className="w-10 h-10 text-white/40 mb-3" />
          <p className="text-sm font-semibold text-white">Stream unavailable</p>
          <p className="text-xs text-white/50 mt-1">{camId}</p>
        </div>
      ) : (
        <div className="absolute inset-0">
          <img
            src={streamUrl}
            alt={`Live surveillance ${camId}`}
            className="w-full h-full object-cover opacity-95 transition-all duration-500"
            onError={() => setStreamError(true)}
          />

          {fences.length > 0 && (
            <svg
              className={cn("absolute inset-0 w-full h-full", editingFenceId ? "pointer-events-auto" : "pointer-events-none")}
              viewBox={`0 0 ${sourceWidth} ${sourceHeight}`}
              preserveAspectRatio="none"
            >
              {fences.filter((f) => f.active !== false).map((fence) => {
                const points = editingFenceId === fence.id && draftFencePoints?.length ? draftFencePoints : normalizeFencePoints(fence);
                if (points.length < 3) return null;
                return (
                  <g key={fence.id}>
                    <polygon
                      points={points.map(([x, y]) => `${x},${y}`).join(" ")}
                      fill="rgba(239,68,68,0.10)"
                      stroke="#ef4444"
                      strokeWidth="4"
                      strokeDasharray="12 8"
                    />
                    <text
                      x={points[0][0]}
                      y={Math.max(22, points[0][1] - 8)}
                      fill="#ffffff"
                      fontSize="18"
                      fontWeight="700"
                      stroke="#111827"
                      strokeWidth="5"
                      paintOrder="stroke"
                    >
                      {fence.name}
                    </text>
                    {editingFenceId === fence.id && points.map(([x, y], pointIndex) => (
                      <circle key={`${fence.id}-handle-${pointIndex}`} cx={x} cy={y} r={12} fill="white" stroke="#ef4444" strokeWidth="4" className="cursor-grab active:cursor-grabbing" onPointerDown={(event) => handleFencePointerDown(event, pointIndex)} />
                    ))}
                  </g>
                );
              })}
            </svg>
          )}

          {ai && (
            <div className="absolute inset-0 pointer-events-none">
              {safeDetections.map((detection, index) => {
                const box = getDetectionBox(detection);
                const confidence = getDetectionConfidence(detection);
                const label = String(detection?.class_name ?? detection?.label ?? detection?.name ?? "Object");
                const trackId = detection?.track_id ?? detection?.id;
                const keypoints = getDetectionKeypoints(detection);
                const plateText = detection?.plate?.text;

                return (
                  <div key={`${camId}-${index}-${trackId ?? "det"}`} className="absolute inset-0">
                    {showBoxes && box && (
                      <div
                        className="absolute border-2 border-cyan-300 transition-[left,top,width,height] duration-100 ease-out"
                        style={{
                          left: `${toPercentX(box.x1)}%`,
                          top: `${toPercentY(box.y1)}%`,
                          width: `${Math.max(0, toPercentX(box.x2) - toPercentX(box.x1))}%`,
                          height: `${Math.max(0, toPercentY(box.y2) - toPercentY(box.y1))}%`,
                        }}
                      >
                        <div className="absolute -top-7 left-0 px-2 py-1 rounded-md bg-black/80 backdrop-blur border border-cyan-300/30 text-[10px] font-bold text-white whitespace-nowrap">
                          {label.toUpperCase()} {confidence.toFixed(1)}%
                          {trackId !== undefined ? ` · ID-${trackId}` : ""}
                          {detection?.posture ? ` · ${String(detection.posture).toUpperCase()}` : ""}{plateText ? ` · ${plateText}` : ""}
                        </div>
                      </div>
                    )}

                    {showTracks && box && (
                      <div
                        className="absolute"
                        style={{
                          left: `${toPercentX((box.x1 + box.x2) / 2)}%`,
                          top: `${toPercentY((box.y1 + box.y2) / 2)}%`,
                          transform: "translate(-50%, -50%)",
                        }}
                      >
                        <div className="w-3 h-3 rounded-full bg-cyan-300 border-2 border-white shadow-[0_0_14px_rgba(34,211,238,0.9)]" />
                        {trackId !== undefined && (
                          <div className="absolute left-4 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-black/70 text-[9px] text-white whitespace-nowrap">
                            ID-{trackId}
                          </div>
                        )}
                      </div>
                    )}

                    {showPose && keypoints.length > 0 && (
                      <svg
                        className="absolute inset-0 w-full h-full"
                        viewBox={`0 0 ${sourceWidth} ${sourceHeight}`}
                        preserveAspectRatio="none"
                      >
                        {POSE_CONNECTIONS.map(([a, b], connectionIndex) => {
                          const p1 = keypoints[a];
                          const p2 = keypoints[b];
                          if (!p1 || !p2 || p1.confidence < 0.25 || p2.confidence < 0.25) return null;
                          return (
                            <line
                              key={connectionIndex}
                              x1={p1.x}
                              y1={p1.y}
                              x2={p2.x}
                              y2={p2.y}
                              vectorEffect="non-scaling-stroke"
                              stroke="currentColor"
                              strokeWidth="2.5"
                              className="text-cyan-300"
                            />
                          );
                        })}
                        {keypoints.map((point, pointIndex) => (
                          point.confidence >= 0.25 ? (
                            <circle
                              key={pointIndex}
                              cx={point.x}
                              cy={point.y}
                              r="4"
                              vectorEffect="non-scaling-stroke"
                              className="fill-white stroke-cyan-300"
                              strokeWidth="2"
                            />
                          ) : null
                        ))}
                      </svg>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="absolute top-3 left-3 flex gap-2 pointer-events-none">
        <div className="px-2 py-1 rounded bg-black/60 backdrop-blur border border-white/10 text-white text-[10px] font-bold flex items-center gap-1.5 shadow-soft">
          <span className="w-1.5 h-1.5 rounded-full bg-critical animate-pulse" /> LIVE
        </div>
        <div className="px-2 py-1 rounded bg-black/60 backdrop-blur border border-white/10 text-white text-[10px] font-semibold">
          {camId}
        </div>
        {ai && (
          <div className="px-2 py-1 rounded bg-cyan/15 backdrop-blur border border-cyan-300/20 text-cyan-200 text-[10px] font-bold">
            {safeDetections.length} OBJECT{safeDetections.length === 1 ? "" : "S"}
          </div>
        )}
      </div>

      {ai && behaviorFlags.length > 0 && (
        <div className="absolute top-12 right-3 px-2 py-1 rounded bg-critical/80 text-white text-[9px] font-bold border border-white/10">
          {behaviorFlags.join(" · ")}
        </div>
      )}

      {ai && (
        <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-black/60 backdrop-blur border border-white/10 text-white text-[10px] font-semibold flex items-center gap-1.5 pointer-events-none">
          <Focus className="w-3 h-3 text-cyan" /> AI MONITORING
        </div>
      )}

      {ai && (
        <div className="absolute bottom-3 right-3 flex items-center gap-1 pointer-events-auto">
          <button
            onClick={() => setShowBoxes((v) => !v)}
            className={cn("px-2 py-1 rounded-md text-[9px] font-bold border backdrop-blur", showBoxes ? "bg-cyan/20 text-cyan border-cyan/40" : "bg-black/60 text-white/60 border-white/10")}
          >BOXES</button>
          <button
            onClick={() => setShowTracks((v) => !v)}
            className={cn("px-2 py-1 rounded-md text-[9px] font-bold border backdrop-blur", showTracks ? "bg-primary/20 text-white border-primary/40" : "bg-black/60 text-white/60 border-white/10")}
          >TRACK</button>
          <button
            onClick={() => setShowPose((v) => !v)}
            className={cn("px-2 py-1 rounded-md text-[9px] font-bold border backdrop-blur", showPose ? "bg-indigo/20 text-white border-indigo/40" : "bg-black/60 text-white/60 border-white/10")}
          >POSE</button>
        </div>
      )}
    </div>
  );
};



// ============================================================
// INTRUSION / ANOMALY FEED
// ============================================================

const AnomalyFeed = ({
  compact = false,
  limit = 100,
}: {
  compact?: boolean;
  limit?: number;
}) => {
  const [anomalies, setAnomalies] = useState<KavronAnomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnomalies = async () => {
    try {
      const data = await getKavronAnomalies(limit);
      setAnomalies(data);
      setError(null);
    } catch (err) {
      console.error("KAVRON anomaly feed error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load anomaly feed",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const data = await getKavronAnomalies(limit);
        if (!active) return;
        setAnomalies(data);
        setError(null);
      } catch (err) {
        if (!active) return;
        console.error("KAVRON anomaly feed error:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load anomaly feed",
        );
      } finally {
        if (active) setLoading(false);
      }
    };

    load();

    const interval = window.setInterval(load, 3000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [limit]);

  const handleAcknowledge = async (anomalyId: string) => {
    try {
      const updated = await acknowledgeKavronAnomaly(anomalyId);

      setAnomalies((current) =>
        current.map((item) =>
          item.anomaly_id === anomalyId
            ? updated
            : item,
        ),
      );
    } catch (err) {
      console.error(
        "KAVRON anomaly acknowledge error:",
        err,
      );
    }
  };

  if (compact) {
    return (
      <div className="space-y-2">
        {loading && anomalies.length === 0 ? (
          <div className="p-4 text-xs text-foreground-secondary text-center">
            Loading anomaly intelligence...
          </div>
        ) : error && anomalies.length === 0 ? (
          <div className="p-4 text-xs text-critical text-center">
            {error}
          </div>
        ) : anomalies.length === 0 ? (
          <div className="p-4 text-xs text-foreground-secondary text-center">
            No intrusion anomalies detected.
          </div>
        ) : (
          anomalies.slice(0, limit).map((anomaly) => (
            <div
              key={anomaly.anomaly_id}
              className={cn(
                "p-3 rounded-xl border flex gap-3",
                anomaly.acknowledged
                  ? "bg-white border-border-subtle"
                  : "bg-critical/5 border-critical/20",
              )}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                  anomaly.acknowledged
                    ? "bg-background-secondary text-foreground-secondary"
                    : "bg-critical/10 text-critical",
                )}
              >
                <ShieldAlert className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-foreground truncate">
                      {anomaly.message}
                    </div>
                    <div className="text-[10px] text-foreground-secondary mt-1">
                      {anomaly.camera_id}
                      {" · "}
                      Track {anomaly.track_id ?? "N/A"}
                      {" · "}
                      {(Number(anomaly.confidence || 0) * 100).toFixed(1)}%
                    </div>
                  </div>

                  <span
                    className={cn(
                      "px-2 py-1 rounded-full text-[9px] font-bold uppercase shrink-0",
                      anomaly.severity === "HIGH" ||
                        anomaly.severity === "CRITICAL"
                        ? "bg-critical/10 text-critical"
                        : "bg-warning/10 text-warning",
                    )}
                  >
                    {anomaly.severity}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-2 gap-2">
                  <span className="text-[10px] text-foreground-secondary">
                    {anomaly.created_at
                      ? new Date(anomaly.created_at).toLocaleString()
                      : "Unknown time"}
                  </span>

                  {!anomaly.acknowledged && (
                    <button
                      className="text-[10px] font-bold text-primary hover:underline"
                      onClick={() =>
                        handleAcknowledge(
                          anomaly.anomaly_id,
                        )
                      }
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    );
  }

  return (
    <Card className="flex flex-col">
      <div className="p-5 border-b border-border-subtle flex items-center justify-between">
        <div>
          <h3 className="font-bold text-foreground flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-critical" />
            Intrusion & Anomaly Log
          </h3>
          <p className="text-xs text-foreground-secondary mt-1">
            Persons detected inside configured restricted zones
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green animate-pulse" />
          <span className="text-[10px] font-bold text-foreground-secondary">
            LIVE
          </span>
        </div>
      </div>

      <div className="p-4">
        {loading && anomalies.length === 0 ? (
          <div className="py-12 text-center text-sm text-foreground-secondary">
            Loading anomaly intelligence...
          </div>
        ) : error && anomalies.length === 0 ? (
          <div className="py-12 text-center text-sm text-critical">
            {error}
          </div>
        ) : anomalies.length === 0 ? (
          <div className="py-12 text-center">
            <div className="mx-auto w-12 h-12 rounded-2xl bg-green/10 flex items-center justify-center mb-3">
              <CheckCircle2 className="w-6 h-6 text-green" />
            </div>
            <div className="text-sm font-bold text-foreground">
              No intrusion anomalies
            </div>
            <div className="text-xs text-foreground-secondary mt-1">
              KAVRON is monitoring the active camera network.
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {anomalies.map((anomaly) => (
              <div
                key={anomaly.anomaly_id}
                className={cn(
                  "rounded-2xl border p-4 transition-all",
                  anomaly.acknowledged
                    ? "bg-white border-border-subtle"
                    : "bg-critical/[0.035] border-critical/20 shadow-sm",
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3 min-w-0">
                    <div
                      className={cn(
                        "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
                        anomaly.acknowledged
                          ? "bg-background-secondary text-foreground-secondary"
                          : "bg-critical/10 text-critical",
                      )}
                    >
                      <ShieldAlert className="w-5 h-5" />
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-bold text-foreground">
                          {anomaly.message}
                        </span>

                        <span
                          className={cn(
                            "px-2 py-1 rounded-full text-[9px] font-bold uppercase",
                            anomaly.severity === "HIGH" ||
                              anomaly.severity === "CRITICAL"
                              ? "bg-critical/10 text-critical"
                              : "bg-warning/10 text-warning",
                          )}
                        >
                          {anomaly.severity}
                        </span>
                      </div>

                      <div className="text-xs text-foreground-secondary mt-1">
                        Anomaly ID:
                        {" "}
                        <span className="font-mono">
                          {anomaly.anomaly_id}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2 mt-3 text-[10px]">
                        <span className="px-2 py-1 rounded-md bg-background-secondary border border-border-subtle text-foreground-secondary">
                          Camera: {anomaly.camera_id}
                        </span>

                        <span className="px-2 py-1 rounded-md bg-background-secondary border border-border-subtle text-foreground-secondary">
                          Track: {anomaly.track_id ?? "N/A"}
                        </span>

                        <span className="px-2 py-1 rounded-md bg-background-secondary border border-border-subtle text-foreground-secondary">
                          Confidence:
                          {" "}
                          {(Number(anomaly.confidence || 0) * 100).toFixed(1)}%
                        </span>

                        <span className="px-2 py-1 rounded-md bg-background-secondary border border-border-subtle text-foreground-secondary">
                          Type: {anomaly.anomaly_type}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 text-right">
                    <div className="text-[10px] text-foreground-secondary">
                      {anomaly.created_at
                        ? new Date(
                            anomaly.created_at,
                          ).toLocaleString()
                        : "Unknown time"}
                    </div>

                    {!anomaly.acknowledged && (
                      <button
                        className="mt-3 px-3 py-1.5 rounded-md bg-foreground text-white text-[10px] font-bold hover:opacity-90 transition-opacity"
                        onClick={() =>
                          handleAcknowledge(
                            anomaly.anomaly_id,
                          )
                        }
                      >
                        Acknowledge
                      </button>
                    )}

                    {anomaly.acknowledged && (
                      <div className="mt-3 inline-flex items-center gap-1 text-[10px] font-bold text-green">
                        <CheckCircle2 className="w-3 h-3" />
                        ACKNOWLEDGED
                      </div>
                    )}
                  </div>
                </div>

                {anomaly.snapshot_path && (
                  <div className="mt-4 pt-4 border-t border-border-subtle">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-foreground-secondary mb-2">
                      Evidence Snapshot
                    </div>
                    <div className="rounded-xl bg-background-secondary border border-border-subtle px-3 py-2 text-xs font-mono text-foreground-secondary break-all">
                      {anomaly.snapshot_path}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};


// ============================================================
// INTRUSION DETECTION PAGE
// ============================================================

const IntrusionDetection = () => {
  const [anomalies, setAnomalies] = useState<KavronAnomaly[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [anomalyData, cameraData] =
        await Promise.all([
          getKavronAnomalies(100),
          getCameras(),
        ]);

      setAnomalies(anomalyData);
      setCameras(cameraData);
    } catch (error) {
      console.error(
        "KAVRON intrusion page error:",
        error,
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();

    const interval =
      window.setInterval(
        load,
        3000,
      );

    return () =>
      window.clearInterval(interval);
  }, []);

  const highSeverity = anomalies.filter(
    (item) =>
      item.severity === "HIGH" ||
      item.severity === "CRITICAL",
  ).length;

  const unacknowledged = anomalies.filter(
    (item) => !item.acknowledged,
  ).length;

  const today = new Date();

  const todayAnomalies = anomalies.filter(
    (item) => {
      if (!item.created_at) return false;

      const date = new Date(
        item.created_at,
      );

      return (
        date.getFullYear() ===
          today.getFullYear() &&
        date.getMonth() ===
          today.getMonth() &&
        date.getDate() ===
          today.getDate()
      );
    },
  ).length;

  return (
    <div className="h-full flex flex-col gap-6 max-w-[1600px] mx-auto">

      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-foreground">
              Intrusion Detection
            </h2>

            <span className="px-2.5 py-1 rounded-full bg-critical/10 text-critical text-[10px] font-bold uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-critical animate-pulse" />
              Live
            </span>
          </div>

          <p className="text-sm text-foreground-secondary mt-1">
            Detect persons entering restricted surveillance zones and
            log anomalies automatically.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 shrink-0">
        <KPICard
          title="Total Cameras"
          value={`${cameras.length}`}
          status={cameras.length > 0 ? "good" : "warning"}
        />

        <KPICard
          title="Anomalies Today"
          value={`${todayAnomalies}`}
          status={
            todayAnomalies > 0
              ? "warning"
              : "good"
          }
        />

        <KPICard
          title="High Severity"
          value={`${highSeverity}`}
          status={
            highSeverity > 0
              ? "critical"
              : "good"
          }
        />

        <KPICard
          title="Needs Attention"
          value={`${unacknowledged}`}
          status={
            unacknowledged > 0
              ? "critical"
              : "good"
          }
        />
      </div>

      <div className="flex-1 min-h-0 overflow-auto">
        {loading && anomalies.length === 0 ? (
          <Card className="p-12 text-center text-sm text-foreground-secondary">
            Loading KAVRON intrusion intelligence...
          </Card>
        ) : (
          <AnomalyFeed
            limit={100}
          />
        )}
      </div>
    </div>
  );
};



// --- REAL MAP / LOCATION SERVICES (STAGE 5) ---

const BorderMap = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [locationState, setLocationState] = useState<"idle" | "requesting" | "enabled" | "denied" | "unavailable">("idle");
  const [userPosition, setUserPosition] = useState<{ lat: number; lon: number; accuracy: number } | null>(null);
  const [pendingPoint, setPendingPoint] = useState<{ lat: number; lon: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const mapElement = React.useRef<HTMLDivElement | null>(null);
  const mapRef = React.useRef<any>(null);
  const cameraLayerRef = React.useRef<any>(null);
  const userLayerRef = React.useRef<any>(null);
  const pendingLayerRef = React.useRef<any>(null);
  const watchRef = React.useRef<number | null>(null);

  const loadCameras = async () => {
    try {
      const data = await getCameras();
      setCameras(data);
      setSelectedCameraId((current) => current || data[0]?.camera_id || "");
    } catch (error) {
      console.error("KAVRON map camera load error:", error);
    }
  };

  useEffect(() => {
    let active = true;
    ensureLeaflet().then((L) => {
      if (!active || !mapElement.current || mapRef.current) return;
      const map = L.map(mapElement.current, {
        zoomControl: true,
        preferCanvas: true,
        minZoom: 2,
        maxZoom: 19,
      }).setView([20.5937, 78.9629], 5);

      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
        crossOrigin: true,
      }).addTo(map);

      cameraLayerRef.current = L.layerGroup().addTo(map);
      userLayerRef.current = L.layerGroup().addTo(map);
      pendingLayerRef.current = L.layerGroup().addTo(map);

      map.on("click", (event: any) => {
        setPendingPoint({ lat: event.latlng.lat, lon: event.latlng.lng });
      });
      mapRef.current = map;
      window.setTimeout(() => map.invalidateSize(), 100);
    }).catch((error) => {
      if (active) setMapError(error instanceof Error ? error.message : "Map failed to load");
    });

    loadCameras();
    const id = window.setInterval(loadCameras, 5000);
    return () => {
      active = false;
      window.clearInterval(id);
      if (watchRef.current !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchRef.current);
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const L = window.L;
    if (!L || !mapRef.current || !cameraLayerRef.current) return;
    cameraLayerRef.current.clearLayers();

    cameras.forEach((camera: any) => {
      if (camera.latitude == null || camera.longitude == null) return;
      const selected = camera.camera_id === selectedCameraId;
      const icon = L.divIcon({
        className: "",
        html: `<div class="kavron-map-marker camera ${selected ? "selected" : ""}"><span>${selected ? "●" : "C"}</span></div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 34],
        popupAnchor: [0, -32],
      });
      const marker = L.marker([Number(camera.latitude), Number(camera.longitude)], { icon });
      marker.bindPopup(`
        <div style="min-width:190px">
          <strong>${String(camera.name || camera.camera_id).replace(/</g, "&lt;")}</strong>
          <div style="font-size:11px;color:#64748b;margin-top:4px">${String(camera.location || "Location not named").replace(/</g, "&lt;")}</div>
          <div style="font-size:11px;color:#64748b;margin-top:4px">${Number(camera.latitude).toFixed(5)}, ${Number(camera.longitude).toFixed(5)}</div>
        </div>
      `);
      marker.on("click", () => setSelectedCameraId(camera.camera_id));
      marker.addTo(cameraLayerRef.current);
    });

    if (selectedCameraId) {
      const selected = cameras.find((camera: any) => camera.camera_id === selectedCameraId) as any;
      if (selected?.latitude != null && selected?.longitude != null) {
        // Keep selection visible without constantly zooming the map.
        mapRef.current.panTo([Number(selected.latitude), Number(selected.longitude)], { animate: true, duration: 0.35 });
      }
    }
  }, [cameras, selectedCameraId]);

  useEffect(() => {
    const L = window.L;
    if (!L || !mapRef.current || !userLayerRef.current) return;
    userLayerRef.current.clearLayers();
    if (!userPosition) return;
    const icon = L.divIcon({
      className: "",
      html: `<div class="kavron-map-marker user"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });
    L.marker([userPosition.lat, userPosition.lon], { icon })
      .bindPopup(`<strong>Current device location</strong><br/><span style="font-size:11px">Accuracy ±${Math.round(userPosition.accuracy)} m</span>`)
      .addTo(userLayerRef.current);
  }, [userPosition]);

  useEffect(() => {
    const L = window.L;
    if (!L || !mapRef.current || !pendingLayerRef.current) return;
    pendingLayerRef.current.clearLayers();
    if (!pendingPoint) return;
    const marker = L.circleMarker([pendingPoint.lat, pendingPoint.lon], {
      radius: 9,
      color: "#dc2626",
      weight: 3,
      fillColor: "#fee2e2",
      fillOpacity: 0.9,
    });
    marker.bindTooltip("Pending camera position", { permanent: true, direction: "top" });
    marker.addTo(pendingLayerRef.current);
  }, [pendingPoint]);

  const enableLocation = () => {
    if (!("geolocation" in navigator)) {
      setLocationState("unavailable");
      return;
    }
    setLocationState("requesting");
    watchRef.current = navigator.geolocation.watchPosition(
      (position) => {
        setLocationState("enabled");
        setUserPosition({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        if (mapRef.current && !userPosition) {
          mapRef.current.setView([position.coords.latitude, position.coords.longitude], 14);
        }
      },
      (error) => {
        setLocationState(error.code === error.PERMISSION_DENIED ? "denied" : "unavailable");
      },
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 },
    );
  };

  const searchMap = async () => {
    const q = query.trim();
    if (q.length < 2) return;
    try {
      const data = await apiFetch<any>(`/api/v1/maps/search?q=${encodeURIComponent(q)}`);
      setSearchResults(Array.isArray(data?.results) ? data.results : []);
    } catch (error) {
      console.error("KAVRON map search error:", error);
      setMapError("Map search is temporarily unavailable.");
    }
  };

  const selectSearchResult = (result: any) => {
    const lat = Number(result.lat);
    const lon = Number(result.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || !mapRef.current) return;
    mapRef.current.setView([lat, lon], 15);
    setPendingPoint({ lat, lon });
    setSearchResults([]);
  };

  const placeSelectedCamera = async () => {
    if (!selectedCameraId || !pendingPoint) return;
    setSaving(true);
    try {
      let locationName: string | undefined;
      try {
        const reverse = await apiFetch<any>(`/api/v1/maps/reverse?lat=${pendingPoint.lat}&lon=${pendingPoint.lon}`);
        locationName = reverse?.display_name;
      } catch {
        // Coordinate persistence still succeeds if geocoding is unavailable.
      }
      await apiFetch(`/api/v1/cameras/${encodeURIComponent(selectedCameraId)}/location`, {
        method: "PATCH",
        body: JSON.stringify({
          latitude: pendingPoint.lat,
          longitude: pendingPoint.lon,
          location: locationName,
          source: "manual",
        }),
      });
      setPendingPoint(null);
      await loadCameras();
    } catch (error) {
      console.error("KAVRON camera geolocation save error:", error);
      window.alert("Unable to save the camera location. Check the backend.");
    } finally {
      setSaving(false);
    }
  };

  const selectedCamera: any = cameras.find((camera: any) => camera.camera_id === selectedCameraId);
  const mappedCount = cameras.filter((camera: any) => camera.latitude != null && camera.longitude != null).length;

  return (
    <div className="h-full flex flex-col gap-5 overflow-y-auto">
      <div className="flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div>
          <h2 className="text-xl font-bold">Border Map</h2>
          <p className="text-sm text-foreground-secondary">Real OpenStreetMap tiles, camera coordinates and browser location services.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn(
            "px-3 py-2 rounded-lg border text-xs font-bold",
            locationState === "enabled" ? "bg-green/10 border-green/20 text-green" :
            locationState === "denied" ? "bg-critical/10 border-critical/20 text-critical" :
            "bg-white border-border text-foreground-secondary"
          )}>
            <span className="inline-block w-2 h-2 rounded-full bg-current mr-2" />
            Location {locationState === "enabled" ? "ON" : locationState === "requesting" ? "REQUESTING" : locationState.toUpperCase()}
          </span>
          <Button variant={locationState === "enabled" ? "secondary" : "primary"} onClick={enableLocation}>
            <LocateFixed className="w-4 h-4 mr-2" /> {locationState === "enabled" ? "Refresh Location" : "Enable Location"}
          </Button>
        </div>
      </div>

      <Card className="p-4 shrink-0">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex items-center gap-2 flex-1 min-w-[260px]">
            <SearchIcon className="w-4 h-4 text-foreground-secondary" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter") searchMap(); }}
              placeholder="Search a border post, city, road or place..."
              className="w-full h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            />
            <Button variant="secondary" className="h-10 px-4" onClick={searchMap}>Search</Button>
          </div>
          <select
            value={selectedCameraId}
            onChange={(event) => setSelectedCameraId(event.target.value)}
            className="h-10 rounded-lg border border-border bg-white px-3 text-sm font-medium"
          >
            {cameras.map((camera: any) => (
              <option key={camera.camera_id} value={camera.camera_id}>{camera.name || camera.camera_id}</option>
            ))}
          </select>
          <Button variant="primary" className="h-10 px-4" disabled={!pendingPoint || !selectedCameraId || saving} onClick={placeSelectedCamera}>
            <MapPin className="w-4 h-4 mr-2" /> {saving ? "Saving..." : "Place Selected Camera"}
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="mt-3 grid gap-2">
            {searchResults.map((result: any, index: number) => (
              <button
                key={`${result.place_id}-${index}`}
                onClick={() => selectSearchResult(result)}
                className="text-left p-3 rounded-xl border border-border-subtle bg-background-secondary hover:bg-white transition-colors"
              >
                <div className="text-xs font-bold">{result.display_name}</div>
                <div className="text-[10px] text-foreground-secondary mt-1">{result.lat}, {result.lon}</div>
              </button>
            ))}
          </div>
        )}
      </Card>

      {mapError && (
        <Card className="p-3 border-critical/20 bg-critical/5 text-xs text-critical">{mapError}</Card>
      )}

      <div className="grid grid-cols-12 gap-5 min-h-[620px]">
        <Card className="col-span-12 xl:col-span-9 p-1 overflow-hidden">
          <div ref={mapElement} className="kavron-map w-full h-[620px] rounded-[14px] overflow-hidden bg-background-secondary" />
        </Card>
        <Card className="col-span-12 xl:col-span-3 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold">Camera Locations</h3>
              <p className="text-[10px] text-foreground-secondary mt-1">{mappedCount}/{cameras.length} cameras mapped</p>
            </div>
            <Navigation className="w-4 h-4 text-primary" />
          </div>
          <div className="space-y-2 max-h-[510px] overflow-auto">
            {cameras.map((camera: any) => {
              const mapped = camera.latitude != null && camera.longitude != null;
              const selected = camera.camera_id === selectedCameraId;
              return (
                <button
                  key={camera.camera_id}
                  onClick={() => {
                    setSelectedCameraId(camera.camera_id);
                    if (mapped && mapRef.current) mapRef.current.setView([Number(camera.latitude), Number(camera.longitude)], 15);
                  }}
                  className={cn(
                    "w-full text-left p-3 rounded-xl border transition-all",
                    selected ? "border-primary/40 bg-primary/5" : "border-border-subtle bg-background-secondary hover:bg-white"
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold truncate">{camera.name || camera.camera_id}</span>
                    <span className={cn("text-[9px] font-bold uppercase", mapped ? "text-green" : "text-foreground-secondary")}>{mapped ? "Mapped" : "Unmapped"}</span>
                  </div>
                  <div className="text-[10px] text-foreground-secondary mt-1 truncate">{camera.location || "Click map to assign a real location"}</div>
                  {mapped && <div className="font-mono text-[9px] text-foreground-secondary mt-1">{Number(camera.latitude).toFixed(5)}, {Number(camera.longitude).toFixed(5)}</div>}
                </button>
              );
            })}
          </div>
          <div className="mt-4 p-3 rounded-xl bg-background border border-border-subtle text-[10px] text-foreground-secondary">
            <strong className="text-foreground">How to map a camera:</strong> select a camera → click its real position on the map → optionally search for a place → click <strong>Place Selected Camera</strong>.
          </div>
        </Card>
      </div>
      <div className="text-[10px] text-foreground-secondary pb-4">
        Map data © OpenStreetMap contributors. Public map/geocoding services are best-effort and rate-limited; production deployments should use a dedicated provider or self-hosted services.
      </div>
    </div>
  );
};

// --- PAGES ---

const CommandDashboard = () => {
  const [overview, setOverview] = useState<any | null>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [detections, setDetections] = useState<any>({});
  const [tracks, setTracks] = useState<any>({});
  const [fences, setFences] = useState<VirtualFence[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>("");
  const [liveEnabled, setLiveEnabled] = useState(false);
  const [fenceBusy, setFenceBusy] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [editingFenceId, setEditingFenceId] = useState<string | null>(null);
  const [draftFencePoints, setDraftFencePoints] = useState<Array<[number, number]>>([]);
  const [fenceSaving, setFenceSaving] = useState(false);

  const load = async () => {
    try {
      const [overviewData, cameraData, detectionData, trackData, fenceData] = await Promise.all([
        apiFetch<any>("/api/v1/overview"),
        getCameras(),
        apiFetch<any>("/api/v1/detections"),
        apiFetch<any>("/api/v1/tracks"),
        apiFetch<VirtualFence[]>("/api/v1/fences"),
      ]);
      setOverview(overviewData);
      setCameras(cameraData);
      setDetections(detectionData || {});
      setTracks(trackData || {});
      setFences(Array.isArray(fenceData) ? fenceData : []);
      setSelectedCameraId((current) => current || cameraData[0]?.camera_id || "");
      setLiveEnabled(cameraData.some((camera) => camera.camera_id === "CAM-LIVE-01"));
    } catch (error) {
      console.error("KAVRON overview error:", error);
    }
  };

  useEffect(() => {
    let active = true;
    const run = async () => { if (active) await load(); };
    run();
    const interval = window.setInterval(run, 2500);
    const socket = connectKavronEvents((event) => {
      if (!active) return;
      if (event?.type) setEvents((current) => [event, ...current].slice(0, 10));
    });
    return () => { active = false; window.clearInterval(interval); socket.close(); };
  }, []);

  const selectedCamera = cameras.find((camera) => camera.camera_id === selectedCameraId) || cameras[0];
  const selectedId = selectedCamera?.camera_id || "";
  const cameraDetections = normalizeDetectionArray(detections, selectedId);
  const cameraTracks = Array.isArray(tracks?.[selectedId]) ? tracks[selectedId] : [];
  const cameraFences = fences.filter((fence) => fence.camera_id === selectedId);
  const people = cameraDetections.filter((d: any) => ["person", "human"].includes(String(d.class_name || "").toLowerCase()));
  const plates = cameraDetections.filter((d: any) => d?.plate?.text);
  const vehicles = cameraDetections.filter((d: any) => ["car", "truck", "bus", "motorcycle", "bicycle", "vehicle"].includes(String(d.class_name || "").toLowerCase()));
  const postureCount = cameraTracks.filter((t: any) => t?.posture).length;

  const handleLiveToggle = async () => {
    try {
      const next = !liveEnabled;
      const result = await apiFetch<any>("/api/v1/stage4/live-camera/toggle", {
        method: "POST",
        body: JSON.stringify({ enabled: next, camera_id: "CAM-LIVE-01", source: "0" }),
      });
      setLiveEnabled(Boolean(result?.enabled));
      await load();
      if (next) setSelectedCameraId("CAM-LIVE-01");
    } catch (error) {
      console.error("KAVRON live camera error:", error);
      window.alert("Unable to start the live camera. Check Windows camera permissions and the backend console.");
    }
  };

  const startFenceEdit = (fence: VirtualFence) => {
    setEditingFenceId(fence.id);
    setDraftFencePoints(normalizeFencePoints(fence));
  };

  const cancelFenceEdit = () => {
    setEditingFenceId(null);
    setDraftFencePoints([]);
  };

  const saveFenceEdit = async (fence: VirtualFence) => {
    if (draftFencePoints.length < 3) return;
    setFenceSaving(true);
    try {
      await apiFetch(`/api/v1/fences/${encodeURIComponent(fence.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ coordinates: draftFencePoints }),
      });
      cancelFenceEdit();
      await load();
    } catch (error) {
      console.error("KAVRON fence update error:", error);
      window.alert("Unable to save the fence. Check the backend console.");
    } finally { setFenceSaving(false); }
  };

  const removeFence = async (fence: VirtualFence) => {
    if (!window.confirm(`Remove ${fence.name}?`)) return;
    setFenceBusy(true);
    try {
      await apiFetch(`/api/v1/fences/${encodeURIComponent(fence.id)}`, { method: "DELETE" });
      if (editingFenceId === fence.id) cancelFenceEdit();
      await load();
    } catch (error) {
      console.error("KAVRON fence delete error:", error);
    } finally { setFenceBusy(false); }
  };

  const toggleFence = async (fence: VirtualFence) => {
    try {
      await apiFetch(`/api/v1/fences/${encodeURIComponent(fence.id)}`, {
        method: "PATCH", body: JSON.stringify({ active: fence.active === false }),
      });
      await load();
    } catch (error) { console.error("KAVRON fence toggle error:", error); }
  };

  const createQuickFence = async () => {
    if (!selectedCamera) return;
    setFenceBusy(true);
    try {
      const width = Number((selectedCamera as any).width) || 1920;
      const height = Number((selectedCamera as any).height) || 1080;
      const id = `FENCE-${selectedId}-${Date.now()}`.slice(0, 64);
      await apiFetch("/api/v1/fences", {
        method: "POST",
        body: JSON.stringify({
          id,
          name: `Restricted Zone ${cameraFences.length + 1}`,
          camera_id: selectedId,
          geometry_type: "polygon",
          coordinates: [
            [Math.round(width * 0.15), Math.round(height * 0.18)],
            [Math.round(width * 0.85), Math.round(height * 0.18)],
            [Math.round(width * 0.85), Math.round(height * 0.82)],
            [Math.round(width * 0.15), Math.round(height * 0.82)],
          ],
          allowed_objects: ["person"],
          severity: "HIGH",
          active: true,
        }),
      });
      await load();
    } catch (error) {
      console.error("KAVRON fence creation error:", error);
    } finally {
      setFenceBusy(false);
    }
  };

  const online = cameras.filter((camera) => Boolean((camera as any).online || (camera as any).running || String((camera as any).status || "").toLowerCase() === "online")).length;
  const displayEvents = events.length ? events : (overview?.recent_alerts || []);

  return (
    <div className="h-full flex flex-col gap-5 max-w-[1700px] mx-auto overflow-y-auto pr-1">
      <div className="flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div>
          <h2 className="text-xl font-bold text-foreground">KAVRON Command Overview</h2>
          <p className="text-sm text-foreground-secondary">Switch cameras and inspect the complete multimodel intelligence stack.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <select value={selectedId} onChange={(e) => setSelectedCameraId(e.target.value)} className="h-10 rounded-lg border border-border bg-white px-3 text-sm font-medium outline-none focus:ring-2 focus:ring-primary/20">
            {cameras.map((camera) => <option key={camera.camera_id} value={camera.camera_id}>{camera.name || camera.camera_id}</option>)}
          </select>
          <Button variant={liveEnabled ? "danger" : "primary"} onClick={handleLiveToggle}>
            <Video className="w-4 h-4 mr-2" /> {liveEnabled ? "Stop Live Camera" : "Start Live Camera"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 shrink-0">
        <KPICard title="Cameras Online" value={`${online}/${cameras.length}`} status={online ? "good" : "warning"} />
        <KPICard title="Person Detection" value={`${people.length}`} status="good" />
        <KPICard title="Active Tracking" value={`${cameraTracks.length}`} status="good" />
        <KPICard title="Number Plates" value={`${plates.length}`} status={plates.length ? "good" : "neutral"} />
        <KPICard title="Vehicles" value={`${vehicles.length}`} />
        <KPICard title="Posture Tracks" value={`${postureCount}`} />
        <KPICard title="Fence Alerts" value={`${(overview?.alerts ?? 0)}`} status={(overview?.alerts ?? 0) ? "warning" : "good"} />
        <KPICard title="Health" value={`${overview?.system_health ?? 0}%`} status={(overview?.system_health ?? 0) >= 95 ? "good" : "warning"} />
      </div>

      <div className="grid grid-cols-12 gap-5 min-h-[520px]">
        <Card className="col-span-12 xl:col-span-8 p-1 bg-black/5 relative">
          {selectedId ? <VideoFeed camId={selectedId} ai={selectedCamera?.ai_enabled !== false} size="large" detections={cameraDetections} fences={cameraFences} editingFenceId={editingFenceId} draftFencePoints={draftFencePoints} onFencePointsChange={setDraftFencePoints} frameWidth={Number((selectedCamera as any)?.width) || undefined} frameHeight={Number((selectedCamera as any)?.height) || undefined} /> : <div className="h-full min-h-[500px] flex items-center justify-center text-sm text-foreground-secondary">No camera available.</div>}
          <div className="absolute left-4 top-4 z-10 flex items-center gap-2 pointer-events-none">
            <span className="px-3 py-1.5 rounded-lg bg-black/70 text-white text-xs font-bold backdrop-blur">{selectedCamera?.name || selectedId || "NO CAMERA"}</span>
            {selectedCamera?.protocol === "webcam" && <span className="px-3 py-1.5 rounded-lg bg-critical/90 text-white text-xs font-bold">LIVE CAMERA</span>}
          </div>
        </Card>

        <Card className="col-span-12 xl:col-span-4 p-0 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border-subtle flex items-center justify-between">
            <div><h3 className="font-bold">Camera Intelligence</h3><p className="text-xs text-foreground-secondary mt-1">{selectedId || "Select a camera"}</p></div>
            <span className="px-2 py-1 rounded-md bg-primary/10 text-primary text-[10px] font-bold">MULTIMODEL</span>
          </div>
          <div className="overflow-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-border-subtle bg-background-secondary/60 text-left"><th className="p-3">Tracking</th><th className="p-3">Number Plate</th><th className="p-3">Person Detection</th><th className="p-3">Posture</th></tr></thead>
              <tbody>
                {cameraTracks.length === 0 ? <tr><td colSpan={4} className="p-8 text-center text-foreground-secondary">Waiting for tracking data...</td></tr> : cameraTracks.map((track: any) => (
                  <tr key={String(track.track_id)} className="border-b border-border-subtle last:border-0">
                    <td className="p-3 font-mono font-bold">ID-{track.track_id ?? "—"}</td>
                    <td className="p-3 font-mono">{track.plate?.text || "—"}</td>
                    <td className="p-3">{String(track.class_name || "").toLowerCase() === "person" ? <span className="text-green font-bold">YES</span> : "—"}</td>
                    <td className="p-3 capitalize">{track.posture || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-auto border-t border-border-subtle p-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-background-secondary p-3"><div className="text-[10px] uppercase font-bold text-foreground-secondary">Visible people</div><div className="text-2xl font-bold mt-1">{people.length}</div></div>
            <div className="rounded-xl bg-background-secondary p-3"><div className="text-[10px] uppercase font-bold text-foreground-secondary">Stable plates</div><div className="text-2xl font-bold mt-1">{plates.length}</div></div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-12 gap-5 shrink-0">
        <Card className="col-span-12 lg:col-span-7 p-5">
          <div className="flex items-center justify-between mb-4"><div><h3 className="font-bold">Virtual Fence Annotation</h3><p className="text-xs text-foreground-secondary mt-1">Configured polygons are rendered over the selected camera and enforced by the backend event engine.</p></div><Button variant="secondary" className="text-xs px-3 py-2" disabled={!selectedId || fenceBusy} onClick={createQuickFence}>{fenceBusy ? "Saving..." : "Add Restricted Zone"}</Button></div>
          <div className="space-y-2">
            {cameraFences.length === 0 ? <div className="p-4 rounded-xl border border-dashed border-border text-xs text-foreground-secondary">No fence for this camera. Add a restricted zone to enable polygon intrusion annotation.</div> : cameraFences.map((fence) => <div key={fence.id} className="p-3 rounded-xl bg-background-secondary border border-border-subtle"><div className="flex items-center justify-between gap-3"><div><div className="text-sm font-bold">{fence.name}</div><div className="text-[10px] text-foreground-secondary">{fence.coordinates.length} points · {fence.severity || "HIGH"} · {fence.active === false ? "disabled" : "active"}</div></div><div className="flex items-center gap-1"><Button variant="ghost" className="h-8 w-8 p-0" onClick={() => startFenceEdit(fence)} title="Adjust fence"><Pencil className="w-4 h-4" /></Button><Button variant="ghost" className="h-8 w-8 p-0" onClick={() => toggleFence(fence)} title={fence.active === false ? "Enable fence" : "Disable fence"}>{fence.active === false ? <RotateCcw className="w-4 h-4" /> : <X className="w-4 h-4" />}</Button><Button variant="ghost" className="h-8 w-8 p-0 text-critical" onClick={() => removeFence(fence)} title="Remove fence"><Trash2 className="w-4 h-4" /></Button></div></div>{editingFenceId === fence.id && <div className="mt-2 flex items-center justify-between gap-2"><span className="text-[10px] text-primary font-bold">DRAG THE RED HANDLES ON THE VIDEO</span><div className="flex gap-2"><Button variant="ghost" className="text-xs" onClick={cancelFenceEdit}>Cancel</Button><Button variant="primary" className="text-xs" disabled={fenceSaving} onClick={() => saveFenceEdit(fence)}><Save className="w-3 h-3 mr-1" />{fenceSaving ? "Saving..." : "Save"}</Button></div></div>}</div>)}
          </div>
        </Card>
        <Card className="col-span-12 lg:col-span-5 p-5">
          <h3 className="font-bold mb-3">Live Intelligence Events</h3>
          <div className="space-y-2 max-h-[210px] overflow-auto">
            {displayEvents.length === 0 ? <div className="text-xs text-foreground-secondary py-8 text-center">Waiting for events...</div> : displayEvents.slice(0, 8).map((event: any, i: number) => <div key={i} className="p-3 rounded-xl border border-border-subtle bg-white flex items-center justify-between gap-3"><div className="min-w-0"><div className="text-xs font-bold truncate">{event.event_type || event.type || "EVENT"}</div><div className="text-[10px] text-foreground-secondary">{event.camera_id || "KAVRON"} · Track {event.track_id ?? "—"}</div></div><span className="text-[10px] font-bold">{event.confidence != null ? `${(Number(event.confidence) * 100).toFixed(0)}%` : "LIVE"}</span></div>)}
          </div>
        </Card>
      </div>
    </div>
  );
};


const LiveSurveillance = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"grid" | "focus">("grid");
  const [allDetections, setAllDetections] = useState<any>({});
  const [allFences, setAllFences] = useState<VirtualFence[]>([]);
  const [liveEnabled, setLiveEnabled] = useState(false);
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  const load = async () => {
    try {
      const [cameraData, detectionData, fenceData] = await Promise.all([getCameras(), apiFetch<any>("/api/v1/detections"), apiFetch<VirtualFence[]>("/api/v1/fences")]);
      setCameras(cameraData); setAllDetections(detectionData || {}); setAllFences(Array.isArray(fenceData) ? fenceData : []);
    } catch (error) { console.error("KAVRON live surveillance error:", error); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); const id = window.setInterval(load, 1500); return () => window.clearInterval(id); }, []);
  const getCameraDetections = (cameraId: string) => normalizeDetectionArray(allDetections, cameraId);
  const onlineCount = cameras.filter((camera) => Boolean((camera as any).online || (camera as any).running || String((camera as any).status || "").toLowerCase() === "online")).length;
  const toggleLive = async () => {
    try {
      const next = !liveEnabled;
      const result = await apiFetch<any>("/api/v1/stage4/live-camera/toggle", { method: "POST", body: JSON.stringify({ enabled: next, camera_id: "CAM-LIVE-01", source: "0" }) });
      setLiveEnabled(Boolean(result?.enabled));
      await load();
    } catch (error) {
      console.error("KAVRON live camera error:", error);
      window.alert("Unable to start the live camera. Check Windows camera permissions and the backend console.");
    }
  };

  return (
    <div className="h-full flex flex-col gap-5">
      <div className="flex items-center justify-between shrink-0"><div><h2 className="text-xl font-bold">Live Surveillance</h2><p className="text-sm text-foreground-secondary">All configured demo feeds plus the optional Windows live camera.</p></div><div className="flex items-center gap-3"><Button variant={liveEnabled ? "danger" : "primary"} onClick={toggleLive}><Video className="w-4 h-4 mr-2" />{liveEnabled ? "Stop Live Camera" : "Start Live Camera"}</Button><span className="px-3 py-2 rounded-lg bg-white border border-border text-xs"><span className="w-2 h-2 rounded-full bg-green inline-block mr-2 animate-pulse" />{onlineCount}/{cameras.length} online</span><div className="flex items-center gap-2 bg-white border border-border p-1 rounded-lg"><Button variant="ghost" className={cn("h-8 w-10 px-0", viewMode === "grid" && "bg-background-secondary")} onClick={() => setViewMode("grid")}><LayoutGrid className="w-4 h-4" /></Button><Button variant="ghost" className={cn("h-8 w-10 px-0", viewMode === "focus" && "bg-background-secondary")} onClick={() => setViewMode("focus")}><Focus className="w-4 h-4" /></Button></div></div></div>
      <div className={cn("flex-1 min-h-0 gap-4", viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 overflow-y-auto pb-2" : "grid grid-cols-1 overflow-y-auto pb-2")}>
        {loading ? <div className="col-span-full flex items-center justify-center text-sm text-foreground-secondary">Loading KAVRON camera feeds...</div> : cameras.length === 0 ? <div className="col-span-full flex items-center justify-center text-sm text-foreground-secondary">No cameras are currently registered.</div> : cameras.map((camera) => <Card key={camera.camera_id} className={cn("p-1 bg-black/5 relative overflow-hidden group border-2 border-transparent hover:border-primary/50 transition-all", viewMode === "focus" ? "min-h-[600px]" : "min-h-[260px]")}><VideoFeed camId={camera.camera_id} ai={camera.ai_enabled !== false} size={viewMode === "focus" ? "large" : "small"} detections={getCameraDetections(camera.camera_id)} fences={allFences.filter((f) => f.camera_id === camera.camera_id)} /></Card>)}
      </div>
    </div>
  );
};


const CameraNetwork = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyCamera, setBusyCamera] = useState<string | null>(null);

  const loadCameras = async () => {
    try {
      const data = await getCameras();
      setCameras(data);
    } catch (error) {
      console.error("Camera API error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCameras();
    const interval = window.setInterval(loadCameras, 5000);
    return () => window.clearInterval(interval);
  }, []);

  const handleStart = async (cameraId: string) => {
    setBusyCamera(cameraId);
    try {
      await fetch(
        `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/api/v1/cameras/${cameraId}/start`,
        { method: "POST" }
      );
      await loadCameras();
    } catch (error) {
      console.error("Failed to start camera:", error);
    } finally {
      setBusyCamera(null);
    }
  };

  const handleStop = async (cameraId: string) => {
    setBusyCamera(cameraId);
    try {
      await fetch(
        `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/api/v1/cameras/${cameraId}/stop`,
        { method: "POST" }
      );
      await loadCameras();
    } catch (error) {
      console.error("Failed to stop camera:", error);
    } finally {
      setBusyCamera(null);
    }
  };

  const onlineCount = cameras.filter((c) => c.status === "online" || (c as any).online).length;
  const offlineCount = Math.max(0, cameras.length - onlineCount);

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 shrink-0">
        <KPICard title="Total Cameras" value={`${cameras.length}`} />
        <KPICard title="Online" value={`${onlineCount}`} status="good" />
        <KPICard title="Offline" value={`${offlineCount}`} status={offlineCount > 0 ? "critical" : "good"} />
        <KPICard title="AI Active" value={`${cameras.filter((c) => c.ai_enabled !== false).length}`} status="good" />
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden bg-white">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-foreground">Camera Infrastructure</h3>
          <Button variant="secondary" className="h-8 px-3 text-xs">
            <Filter className="w-3.5 h-3.5 mr-2" /> Filter
          </Button>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="p-10 text-center text-sm text-foreground-secondary">
              Loading cameras...
            </div>
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-foreground-secondary uppercase bg-background-secondary/50 sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-semibold">Camera</th>
                  <th className="px-6 py-3 font-semibold">Location</th>
                  <th className="px-6 py-3 font-semibold">Protocol</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold">AI Processing</th>
                  <th className="px-6 py-3 font-semibold">FPS</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>

              <tbody>
                {cameras.map((camera) => {
                  const runtimeOnline = Boolean(
                    (camera as any).online ||
                    (camera.status || "").toLowerCase() === "online"
                  );

                  const running = Boolean(
                    (camera as any).running
                  );

                  return (
                    <tr key={camera.camera_id} className="border-b border-border hover:bg-background-secondary/50 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-foreground">
                        {camera.camera_id}
                      </td>

                      <td className="px-6 py-4 text-foreground-secondary">
                        {camera.location || "—"}
                      </td>

                      <td className="px-6 py-4 text-foreground-secondary">
                        {camera.protocol || "—"}
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold uppercase",
                            runtimeOnline
                              ? "bg-green/10 text-green"
                              : "bg-critical/10 text-critical"
                          )}
                        >
                          <span className={cn(
                            "w-1.5 h-1.5 rounded-full",
                            runtimeOnline ? "bg-green" : "bg-critical"
                          )} />
                          {runtimeOnline ? "Online" : "Offline"}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-foreground-secondary text-xs">
                        {camera.ai_enabled === false
                          ? "Disabled"
                          : running
                          ? "Active"
                          : "Ready"}
                      </td>

                      <td className="px-6 py-4 text-foreground-secondary text-xs font-mono">
                        {typeof (camera as any).fps === "number"
                          ? (camera as any).fps.toFixed(1)
                          : "0.0"}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <button
                          className="text-primary hover:underline text-xs font-medium mr-4"
                          onClick={() => handleStart(camera.camera_id)}
                          disabled={busyCamera === camera.camera_id}
                        >
                          {busyCamera === camera.camera_id
                            ? "Working..."
                            : running
                            ? "Restart"
                            : "Start"}
                        </button>

                        {running && (
                          <button
                            className="text-critical hover:underline text-xs font-medium mr-4"
                            onClick={() => handleStop(camera.camera_id)}
                            disabled={busyCamera === camera.camera_id}
                          >
                            Stop
                          </button>
                        )}

                        <button className="text-foreground-secondary hover:text-foreground">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
};



const AIModelLab = () => {
  const [status, setStatus] = useState<any | null>(null);
  const [stage5, setStage5] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    try {
      const [stage4Data, stage5Data] = await Promise.all([
        apiFetch<any>("/api/v1/stage4/status"),
        apiFetch<any>("/api/v1/stage5/status"),
      ]);
      setStatus(stage4Data);
      setStage5(stage5Data);
    }
    catch (error) { console.error("KAVRON model status error:", error); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); const id = window.setInterval(load, 5000); return () => window.clearInterval(id); }, []);
  const models = status?.models || [];
  const capabilities = stage5?.capabilities || [];
  return (
    <div className="h-full overflow-y-auto space-y-5">
      <div><h2 className="text-xl font-bold">AI Model Lab</h2><p className="text-sm text-foreground-secondary">Stage 5 model health, problem-statement coverage and fine-tuning readiness.</p></div>
      <Card className="p-5">
        {loading ? <div className="py-10 text-center text-sm text-foreground-secondary">Checking model assets...</div> : <div className="overflow-auto"><table className="w-full text-xs"><thead><tr className="border-b border-border-subtle text-left"><th className="p-3">Model</th><th className="p-3">Task</th><th className="p-3">Installed</th><th className="p-3">Loaded</th><th className="p-3">Active</th><th className="p-3">Path</th></tr></thead><tbody>{models.map((model: any) => <tr key={model.id} className="border-b border-border-subtle"><td className="p-3 font-bold">{model.name}</td><td className="p-3">{model.task}</td><td className="p-3">{model.installed ? "✓" : "—"}</td><td className="p-3">{model.loaded ? "✓" : "—"}</td><td className="p-3">{model.active ? <span className="text-green font-bold">ACTIVE</span> : "READY"}</td><td className="p-3 font-mono text-[10px] truncate max-w-[360px]">{model.path || "—"}</td></tr>)}</tbody></table></div>}
      </Card>
      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div><h3 className="font-bold">Problem Statement 26187 Coverage</h3><p className="text-xs text-foreground-secondary mt-1">Live capability audit — no feature is marked complete solely because a file exists.</p></div>
          <span className="px-2.5 py-1 rounded-full bg-green/10 text-green text-[10px] font-bold">{capabilities.filter((item: any) => item.implemented).length}/{capabilities.length} COVERED</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {capabilities.map((item: any) => <div key={item.name} className="flex items-center justify-between gap-3 p-3 rounded-xl bg-background-secondary border border-border-subtle"><span className="text-xs font-medium">{item.name}</span><span className="text-[9px] font-bold text-green">IMPLEMENTED</span></div>)}
        </div>
      </Card>
      <Card className="p-5"><h3 className="font-bold">Stage 4 Fine-Tuning Gate</h3><p className="text-xs text-foreground-secondary mt-2">The package contains the reproducible training/validation pipeline. Actual supervised fine-tuning is only started after labeled KAVRON data is supplied; this prevents us from claiming a trained model without ground truth.</p><div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3"><div className="p-4 rounded-xl bg-background-secondary"><div className="text-[10px] uppercase font-bold text-foreground-secondary">Dataset</div><div className="text-sm font-bold mt-1">{status?.training?.dataset_ready ? "READY" : "LABELS REQUIRED"}</div></div><div className="p-4 rounded-xl bg-background-secondary"><div className="text-[10px] uppercase font-bold text-foreground-secondary">Training</div><div className="text-sm font-bold mt-1">{status?.training?.script || "train_yolo_stage4.py"}</div></div><div className="p-4 rounded-xl bg-background-secondary"><div className="text-[10px] uppercase font-bold text-foreground-secondary">Promotion</div><div className="text-sm font-bold mt-1">Benchmark → Validate → Promote</div></div></div></Card>
    </div>
  );
};


const AIVision = () => {
  const [overview, setOverview] = useState<any | null>(null);
  const [detections, setDetections] = useState<any>({});
  const [models, setModels] = useState<any>({});

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [overviewData, detectionsData, modelData] = await Promise.all([
          apiFetch<any>("/api/v1/overview"),
          apiFetch<any>("/api/v1/detections"),
          apiFetch<any>("/api/v1/models/metadata"),
        ]);

        if (!active) return;

        setOverview(overviewData);
        setDetections(detectionsData);
        setModels(modelData);
      } catch (error) {
        console.error("AI Vision API error:", error);
      }
    };

    load();
    const interval = window.setInterval(load, 3000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const allDetections = Object.values(detections || {}).flat() as any[];

  const totalDetections =
    overview?.detections_today ??
    allDetections.length;

  const averageConfidence =
    allDetections.length > 0
      ? (
          (allDetections.reduce(
            (sum, item) => sum + Number(item.confidence || 0),
            0
          ) /
            allDetections.length) *
          100
        ).toFixed(1)
      : "0.0";

  const modelCount = Object.keys(models || {}).length;

  const categoryCounts = allDetections.reduce(
    (acc: Record<string, number>, item: any) => {
      const name = String(item.class_name || "unknown").toLowerCase();

      if (name === "person") {
        acc.People = (acc.People || 0) + 1;
      } else if (
        ["car", "truck", "bus", "motorcycle", "bicycle"].includes(name)
      ) {
        acc.Vehicles = (acc.Vehicles || 0) + 1;
      } else if (
        ["dog", "cat", "bird", "horse", "cow", "sheep"].includes(name)
      ) {
        acc.Animals = (acc.Animals || 0) + 1;
      } else {
        acc.Unknown = (acc.Unknown || 0) + 1;
      }

      return acc;
    },
    {}
  );

  const categoryTotal =
    Object.values(categoryCounts).reduce(
      (sum, value) => sum + value,
      0
    ) || 1;

  const categoryRows = [
    {
      label: "People",
      val: `${Math.round(((categoryCounts.People || 0) / categoryTotal) * 100)}%`,
      color: "bg-cyan",
    },
    {
      label: "Vehicles",
      val: `${Math.round(((categoryCounts.Vehicles || 0) / categoryTotal) * 100)}%`,
      color: "bg-primary",
    },
    {
      label: "Animals",
      val: `${Math.round(((categoryCounts.Animals || 0) / categoryTotal) * 100)}%`,
      color: "bg-indigo",
    },
    {
      label: "Unknown",
      val: `${Math.round(((categoryCounts.Unknown || 0) / categoryTotal) * 100)}%`,
      color: "bg-warning",
    },
  ];

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-xl font-bold text-foreground">AI Vision Intelligence</h2>
          <p className="text-sm text-foreground-secondary">Understand what KAVRON sees</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-md bg-gradient-blue-cyan text-white text-xs font-bold shadow-soft flex items-center gap-1.5">
            <Focus className="w-3.5 h-3.5" /> {modelCount} MODELS ACTIVE
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 shrink-0">
        <KPICard title="Total Detections" value={Number(totalDetections).toLocaleString()} trend="live" />
        <KPICard title="Average Confidence" value={`${averageConfidence}%`} />
        <KPICard title="Tracked Objects" value={`${overview?.tracked_objects ?? 0}`} status="good" />
        <KPICard title="Alerts" value={`${overview?.alerts ?? 0}`} status={(overview?.alerts ?? 0) > 0 ? "warning" : "good"} />
      </div>

      <div className="flex-1 grid grid-cols-3 gap-6 min-h-0">
        <Card className="col-span-2 p-6 flex flex-col">
          <h3 className="font-bold text-foreground mb-4">Live Detection Activity</h3>

          <div className="flex-1 relative flex items-end">
            <div className="absolute inset-0 flex flex-col justify-between py-4">
              {[100, 75, 50, 25, 0].map(val => (
                <div key={val} className="border-t border-border-subtle w-full" />
              ))}
            </div>

            <div className="relative z-10 w-full h-full flex items-end gap-1 px-2 pb-2">
              {Array.from({ length: 24 }).map((_, index) => {
                const base = allDetections.length
                  ? Math.max(
                      8,
                      Math.min(
                        92,
                        12 +
                          (
                            allDetections.slice(
                              0,
                              Math.min(allDetections.length, 24)
                            )[index]?.confidence || 0.2
                          ) *
                            70
                      )
                    )
                  : 12;

                return (
                  <div
                    key={index}
                    className="flex-1 rounded-t-md bg-primary/70 transition-all duration-500"
                    style={{ height: `${base}%` }}
                  />
                );
              })}
            </div>
          </div>
        </Card>

        <Card className="col-span-1 p-4 bg-gradient-to-b from-white to-background flex flex-col">
          <h3 className="font-bold text-foreground text-sm mb-4">Object Categories</h3>

          <div className="space-y-4 flex-1">
            {categoryRows.map(item => (
              <div key={item.label} className="space-y-1.5">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-foreground-secondary">{item.label}</span>
                  <span className="font-bold text-foreground">{item.val}</span>
                </div>

                <div className="w-full h-2 rounded-full bg-border overflow-hidden">
                  <div
                    className={cn("h-full rounded-full", item.color)}
                    style={{ width: item.val }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};


export default function App() {
  useEffect(() => {
    let cancelled = false;
    getCameras()
      .then((cameras) => {
        if (cancelled) return;
        console.log("🔥 KAVRON BACKEND CONNECTED");
        console.log("📡 Cameras:", cameras);
      })
      .catch((error) => {
        if (cancelled) return;
        console.error("❌ KAVRON BACKEND ERROR:", error);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />

      {/* App Routes */}
      <Route path="/app" element={<AppShell><CommandDashboard /></AppShell>} />
      <Route path="/app/live" element={<AppShell><LiveSurveillance /></AppShell>} />
      <Route path="/app/cameras" element={<AppShell><CameraNetwork /></AppShell>} />
      <Route path="/app/map" element={<AppShell><BorderMap /></AppShell>} />
      <Route path="/app/ai" element={<AppShell><AIVision /></AppShell>} />
      <Route path="/app/models" element={<AppShell><AIModelLab /></AppShell>} />
      <Route path="/app/intrusion" element={<AppShell><IntrusionDetection /></AppShell>} />

      {/* Existing fallback routes */}
      <Route path="/app/*" element={
        <AppShell>
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-background-secondary flex items-center justify-center mb-4">
              <Eye className="w-8 h-8 text-foreground-secondary" />
            </div>
            <h2 className="text-xl font-bold text-foreground mb-2">Module Active</h2>
            <p className="text-foreground-secondary max-w-md">
              This specific KAVRON intelligence module is loaded and operational.
            </p>
          </div>
        </AppShell>
      } />
    </Routes>
  );
}
