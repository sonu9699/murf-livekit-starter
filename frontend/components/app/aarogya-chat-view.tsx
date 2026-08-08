'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { MediaDeviceFailure, Track } from 'livekit-client';
import {
  ArrowDownIcon,
  MicIcon,
  MicOffIcon,
  PhoneOffIcon,
  RotateCcwIcon,
  SendHorizontalIcon,
  TriangleAlertIcon,
} from 'lucide-react';
import {
  type AppendMessage,
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  type ThreadMessageLike,
  ThreadPrimitive,
  useAuiState,
  useExternalStoreRuntime,
} from '@assistant-ui/react';
import {
  type AgentState,
  type ReceivedMessage,
  type TrackReferenceOrPlaceholder,
  useChat,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
} from '@livekit/components-react';
import { AgentAudioVisualizerBar } from '@/components/agents-ui/agent-audio-visualizer-bar';
import { AgentAudioVisualizerRadial } from '@/components/agents-ui/agent-audio-visualizer-radial';
import { type OrbTone, VoiceOrb } from '@/components/app/voice-orb';
import { MarkdownText } from '@/components/assistant-ui/markdown-text';
import { Button } from '@/components/ui/button';
import { useInputControls } from '@/hooks/agents-ui/use-agent-control-bar';
import { cn } from '@/lib/shadcn/utils';
import { toastAlert } from '@/lib/toast-alert';

/** State tone — drives the status dot colour and the orb glow. */
type StatusTone = OrbTone | 'muted';

/** Maps the raw agent state to a short, human Hindi status line + tone. */
function statusFor(state: AgentState | undefined): {
  label: string;
  live: boolean;
  tone: StatusTone;
} {
  switch (state) {
    case 'connecting':
    case 'initializing':
      return { label: 'Jud rahe hain…', live: false, tone: 'muted' };
    case 'listening':
      return { label: 'Sun rahi hun…', live: true, tone: 'teal' };
    case 'thinking':
      return { label: 'Soch rahi hun…', live: true, tone: 'indigo' };
    case 'speaking':
      return { label: 'Bol rahi hun…', live: true, tone: 'primary' };
    default:
      return { label: 'Taiyaar hun', live: false, tone: 'muted' };
  }
}

/** Bar colour per tone — the visualizer inherits currentColor. */
const TONE_TEXT: Record<StatusTone, string> = {
  primary: 'text-primary',
  teal: 'text-teal',
  indigo: 'text-indigo',
  muted: 'text-muted-foreground/50',
};

/** Tap-to-ask starter prompts, each colour-coded by topic. */
const STARTER_PROMPTS: { text: string; tone: OrbTone; chip: string; dot: string }[] = [
  {
    text: 'Mujhe do din se bukhaar hai',
    tone: 'teal',
    chip: 'border-teal/40 hover:border-teal hover:bg-teal/10',
    dot: 'bg-teal',
  },
  {
    text: 'Ayushman card kaise banwaun?',
    tone: 'indigo',
    chip: 'border-indigo/40 hover:border-indigo hover:bg-indigo/10',
    dot: 'bg-indigo',
  },
  {
    text: 'Bacche ka agla teeka kab lagega?',
    tone: 'primary',
    chip: 'border-terracotta/40 hover:border-terracotta hover:bg-terracotta/10',
    dot: 'bg-terracotta',
  },
];

/** Small saffron monogram used as the agent's avatar. */
function SaathiAvatar({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        'bg-primary/15 text-primary font-display flex shrink-0 items-center justify-center rounded-full leading-none select-none',
        className
      )}
    >
      A
    </span>
  );
}

/** LiveKit ReceivedMessage → assistant-ui message. */
const convertMessage = (m: ReceivedMessage): ThreadMessageLike => ({
  id: m.id,
  role: m.from?.isLocal ? 'user' : 'assistant',
  content: [{ type: 'text', text: m.message }],
  createdAt: new Date(m.timestamp),
});

export interface AarogyaChatViewProps {
  supportsChatInput?: boolean;
  className?: string;
}

export function AarogyaChatView({
  supportsChatInput = true,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AarogyaChatViewProps) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state, audioTrack } = useVoiceAssistant();
  const { send } = useChat();

  const onNew = useCallback(
    async (message: AppendMessage) => {
      const part = message.content[0];
      if (part?.type !== 'text') return;
      await send(part.text);
    },
    [send]
  );

  const runtime = useExternalStoreRuntime({
    messages,
    isRunning: state === 'thinking',
    convertMessage,
    onNew,
  });

  const status = statusFor(state);

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 flex h-full w-full flex-col', className)}
      {...props}
    >
      {/* Live status — floats under the fixed header wordmark */}
      <div className="pointer-events-none absolute inset-x-0 top-16 z-20 flex justify-center md:top-20">
        <div className="border-border/60 bg-background/80 text-muted-foreground flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[0.65rem] tracking-[0.18em] uppercase backdrop-blur">
          <AgentAudioVisualizerBar
            size="icon"
            state={state}
            audioTrack={audioTrack}
            barCount={4}
            className={cn('h-4', TONE_TEXT[status.tone])}
            aria-hidden
          />
          {status.label}
        </div>
      </div>

      <AssistantRuntimeProvider runtime={runtime}>
        <AarogyaThread
          supportsChatInput={supportsChatInput}
          isThinking={state === 'thinking'}
          state={state}
          audioTrack={audioTrack}
          tone={status.tone === 'muted' ? 'primary' : status.tone}
          onSuggestion={(text) => void send(text)}
          onEnd={session.end}
        />
      </AssistantRuntimeProvider>
    </section>
  );
}

interface AarogyaThreadProps {
  supportsChatInput: boolean;
  isThinking: boolean;
  state: AgentState;
  audioTrack?: TrackReferenceOrPlaceholder;
  tone: OrbTone;
  onSuggestion: (text: string) => void;
  onEnd: () => void;
}

function AarogyaThread({
  supportsChatInput,
  isThinking,
  state,
  audioTrack,
  tone,
  onSuggestion,
  onEnd,
}: AarogyaThreadProps) {
  const [micDenied, setMicDenied] = useState(false);

  // Clear, actionable messages when the browser blocks or can't open the mic.
  const handleDeviceError = useCallback(
    ({ source, error }: { source: Track.Source; error: Error }) => {
      if (source !== Track.Source.Microphone) return;
      switch (MediaDeviceFailure.getFailure(error)) {
        case MediaDeviceFailure.PermissionDenied:
          setMicDenied(true);
          toastAlert({
            variant: 'destructive',
            title: 'Mic access band hai',
            description:
              'Awaaz sunane ke liye microphone chahiye. Browser ke address bar me lock/mic icon dabayein → Microphone → Allow, phir “Dobara koshish karein” par tap karein.',
          });
          break;
        case MediaDeviceFailure.NotFound:
          toastAlert({
            variant: 'destructive',
            title: 'Mic nahi mila',
            description: 'Koi microphone detect nahi hua. Mic laga kar dobara koshish karein.',
          });
          break;
        case MediaDeviceFailure.DeviceInUse:
          toastAlert({
            variant: 'destructive',
            title: 'Mic busy hai',
            description:
              'Microphone kisi aur app (call ya recording) me chal raha hai. Use band karke dobara koshish karein.',
          });
          break;
        default:
          toastAlert({
            variant: 'destructive',
            title: 'Mic chalu nahi ho paya',
            description: 'Kuch takneeki dikkat aa gayi. Dobara koshish karein.',
          });
      }
    },
    []
  );

  const { microphoneToggle } = useInputControls({
    saveUserChoices: true,
    onDeviceError: handleDeviceError,
  });
  const micOn = microphoneToggle.enabled;
  const isLive = state === 'listening' || state === 'thinking' || state === 'speaking';

  // Once the mic is actually on, drop any lingering "denied" notice.
  useEffect(() => {
    if (micOn) setMicDenied(false);
  }, [micOn]);

  const retryMic = useCallback(() => {
    void microphoneToggle.toggle(true);
  }, [microphoneToggle]);

  return (
    <ThreadPrimitive.Root className="flex h-full flex-col">
      <ThreadPrimitive.Viewport className="relative flex-1 overflow-y-auto scroll-smooth">
        <div className="mx-auto flex w-full max-w-2xl flex-col px-4 pt-28 md:pt-32">
          {/* Empty state — greeting + tap-to-ask chips */}
          <ThreadPrimitive.Empty>
            <div className="flex flex-col items-center gap-6 py-6 text-center">
              <VoiceOrb active={isLive} tone={tone} className="size-24">
                <AgentAudioVisualizerBar
                  size="md"
                  state={state}
                  audioTrack={audioTrack}
                  barCount={5}
                  className={cn(TONE_TEXT[tone])}
                />
              </VoiceOrb>
              <div className="space-y-2">
                <p className="font-display text-2xl leading-tight font-light tracking-tight">
                  Namaste! Main Aarogya Saathi hun.
                </p>
                <p className="text-muted-foreground text-sm">
                  Mic dabaiye aur boliye — tabiyat se judi koi bhi baat poochhiye.
                </p>
              </div>
              {supportsChatInput && (
                <div className="flex flex-wrap justify-center gap-2">
                  {STARTER_PROMPTS.map((prompt) => (
                    <button
                      key={prompt.text}
                      type="button"
                      onClick={() => onSuggestion(prompt.text)}
                      className={cn(
                        'text-foreground inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-[transform,border-color,background-color] duration-200 hover:-translate-y-0.5 active:translate-y-0',
                        prompt.chip
                      )}
                    >
                      <span
                        className={cn('size-1.5 shrink-0 rounded-full', prompt.dot)}
                        aria-hidden
                      />
                      {prompt.text}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </ThreadPrimitive.Empty>

          {/* Conversation */}
          <div className="flex flex-col gap-6 pb-44">
            <ThreadPrimitive.Messages>{() => <ThreadMessage />}</ThreadPrimitive.Messages>

            {isThinking && (
              <div className="is-assistant flex w-full gap-3">
                <SaathiAvatar className="mt-0.5 size-8 text-sm" />
                <div className="flex items-center gap-1.5 pt-3">
                  <span className="bg-indigo/70 size-2 rounded-full [animation-delay:-0.3s] motion-safe:animate-bounce" />
                  <span className="bg-indigo/70 size-2 rounded-full [animation-delay:-0.15s] motion-safe:animate-bounce" />
                  <span className="bg-indigo/70 size-2 rounded-full motion-safe:animate-bounce" />
                </div>
              </div>
            )}
          </div>
        </div>

        <ThreadPrimitive.ScrollToBottom asChild>
          <Button
            variant="outline"
            size="icon"
            aria-label="Neeche jayein"
            className="bg-background absolute bottom-40 left-1/2 z-20 size-9 -translate-x-1/2 rounded-full shadow-sm disabled:invisible"
          >
            <ArrowDownIcon className="size-4" />
          </Button>
        </ThreadPrimitive.ScrollToBottom>
      </ThreadPrimitive.Viewport>

      {/* Composer — pinned to the bottom */}
      <div className="from-background pointer-events-none bg-gradient-to-t to-transparent pt-6">
        <div className="pointer-events-auto mx-auto w-full max-w-2xl px-4 pb-[max(1.25rem,env(safe-area-inset-bottom))] md:pb-8">
          {/* Mic permission denied — clear, actionable recovery strip */}
          {micDenied && (
            <div
              role="alert"
              className="border-destructive/40 bg-destructive/10 text-destructive mx-auto mb-3 flex max-w-md items-center gap-3 rounded-2xl border px-4 py-3 text-sm"
            >
              <TriangleAlertIcon className="size-5 shrink-0" aria-hidden />
              <p className="flex-1 leading-snug">
                Mic band hai. Browser ke lock/mic icon me Microphone ko <strong>Allow</strong>{' '}
                karein.
              </p>
              <Button
                type="button"
                size="sm"
                variant="destructive"
                onClick={retryMic}
                className="shrink-0 gap-1.5"
              >
                <RotateCcwIcon className="size-4" />
                Dobara koshish karein
              </Button>
            </div>
          )}

          {supportsChatInput ? (
            /* Voice + text mode — bordered composer bar */
            <ComposerPrimitive.Root className="border-border bg-background focus-within:border-primary/50 flex items-end gap-2 rounded-[26px] border p-2 shadow-sm transition-colors">
              <Button
                type="button"
                size="icon"
                variant={micOn ? 'default' : 'destructive'}
                disabled={microphoneToggle.pending}
                onClick={() => microphoneToggle.toggle(!micOn)}
                aria-label={micOn ? 'Mic band karein' : 'Mic chalu karein'}
                className="size-11 shrink-0 rounded-full transition-transform active:scale-95"
              >
                {micOn ? <MicIcon /> : <MicOffIcon />}
              </Button>

              <ComposerPrimitive.Input
                rows={1}
                autoFocus
                enterKeyHint="send"
                placeholder="Yahan likhiye…"
                aria-label="Sandesh likhein"
                className="text-foreground placeholder:text-muted-foreground max-h-28 min-h-9 flex-1 resize-none bg-transparent px-1 py-2 text-[15px] leading-6 outline-none [scrollbar-width:thin]"
              />
              <ComposerPrimitive.Send asChild>
                <Button
                  type="button"
                  size="icon"
                  aria-label="Bhejein"
                  className="size-11 shrink-0 rounded-full transition-transform active:scale-95"
                >
                  <SendHorizontalIcon />
                </Button>
              </ComposerPrimitive.Send>

              <Button
                type="button"
                size="icon"
                variant="ghost"
                onClick={onEnd}
                aria-label="Baat band karein"
                className="text-destructive hover:bg-destructive/10 hover:text-destructive size-11 shrink-0 rounded-full transition-transform active:scale-95"
              >
                <PhoneOffIcon />
              </Button>
            </ComposerPrimitive.Root>
          ) : (
            /* Voice-only — a reactive mic orb (big-LLM voice style) in the warm
               palette: radial audio bars react to the agent's voice and animate
               per state; the mic is the tap target and end-call is a quiet
               secondary below it. */
            <div className="flex flex-col items-center gap-4">
              <div className="relative size-28">
                <AgentAudioVisualizerRadial
                  size="md"
                  state={state}
                  audioTrack={audioTrack}
                  barCount={24}
                  className="text-primary pointer-events-none absolute inset-0"
                />
                <Button
                  type="button"
                  size="icon"
                  variant={micOn ? 'default' : 'destructive'}
                  disabled={microphoneToggle.pending}
                  onClick={() => microphoneToggle.toggle(!micOn)}
                  aria-label={micOn ? 'Mic band karein' : 'Mic chalu karein'}
                  className="absolute inset-0 z-10 m-auto size-20 shrink-0 rounded-full shadow-lg transition-transform active:scale-95"
                >
                  {micOn ? <MicIcon className="size-7" /> : <MicOffIcon className="size-7" />}
                </Button>
              </div>

              <span className="text-muted-foreground font-mono text-[0.62rem] tracking-[0.2em] uppercase">
                {micOn ? 'Boliye' : 'Mic band hai'}
              </span>

              <Button
                type="button"
                variant="ghost"
                onClick={onEnd}
                className="text-destructive hover:bg-destructive/10 hover:text-destructive mt-1 h-9 gap-2 rounded-full px-4 font-mono text-[0.7rem] tracking-[0.12em] uppercase"
              >
                <PhoneOffIcon className="size-4" />
                Baat band karein
              </Button>
            </div>
          )}

          <p className="text-muted-foreground/70 mt-4 text-center text-[0.7rem]">
            Aarogya Saathi doctor nahi hai. Kisi bhi emergency me turant nazdeeki aspataal jayein.
          </p>
        </div>
      </div>
    </ThreadPrimitive.Root>
  );
}

/** Routes each thread message to a user bubble or an assistant row. */
function ThreadMessage() {
  const role = useAuiState((s) => s.message.role);
  return role === 'user' ? <UserMessage /> : <AssistantMessage />;
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="is-user motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-bottom-2 motion-safe:slide-in-from-right-2 flex w-full justify-end">
      <div className="bg-secondary text-foreground max-w-[80%] rounded-2xl rounded-br-sm px-4 py-2.5 text-[15px] leading-7">
        <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="is-assistant motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-bottom-2 flex w-full gap-3">
      <SaathiAvatar className="mt-0.5 size-8 text-sm" />
      <div className="min-w-0 flex-1">
        <div className="text-muted-foreground mb-1 font-mono text-[0.65rem] tracking-[0.18em] uppercase">
          Aarogya Saathi
        </div>
        <div className="text-foreground text-[15px] leading-7 text-pretty">
          <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}
