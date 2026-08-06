export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Aarogya Saathi',
  pageTitle: 'Aarogya Saathi · Bharat ka voice health saathi',
  pageDescription:
    'Aarogya Saathi — ek Hinglish voice health helper for chhote sheher aur gaon. Symptoms samjho, home-care aur PHC guidance lo, Ayushman Bharat jaisi schemes jaano. Doctor ka replacement nahi.',

  supportsChatInput: true,
  // Voice + text only — a phone health call has no use for camera/screen-share,
  // and dropping them keeps the chat UI clean and avoids extra device prompts.
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  // Header uses a text wordmark (see app/layout.tsx), so no logo image is needed.
  logo: '',
  logoDark: '',
  // Marigold / saffron — warm, trustworthy, distinctly Indian (injected as --primary).
  accent: '#E8853A',
  accentDark: '#F2A65A',
  startButtonText: 'Baat shuru karein',

  // Warm saffron bar visualizer to match the editorial theme.
  audioVisualizerType: 'bar',
  audioVisualizerColor: '#E8853A',
  audioVisualizerColorDark: '#F2A65A',
  audioVisualizerBarCount: 7,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
