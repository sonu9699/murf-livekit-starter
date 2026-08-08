'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AarogyaChatView } from '@/components/app/aarogya-chat-view';
import { CallEndedView } from '@/components/app/call-ended-view';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AarogyaChatView);
const MotionCallEndedView = motion.create(CallEndedView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const [isStarting, setIsStarting] = useState(false);
  const [hasEnded, setHasEnded] = useState(false);

  // Detect the connected → disconnected transition so we can show an explicit
  // "Call ended" screen instead of snapping straight back to Welcome.
  const prevConnected = useRef(false);
  useEffect(() => {
    if (prevConnected.current && !isConnected) {
      setHasEnded(true);
    }
    prevConnected.current = isConnected;
  }, [isConnected]);

  const handleStart = useCallback(async () => {
    setHasEnded(false);
    setIsStarting(true);
    try {
      await start();
    } catch {
      // Connection failed — surfaced by useAgentErrors; fall back to Welcome.
    } finally {
      setIsStarting(false);
    }
  }, [start]);

  const handleHome = useCallback(() => setHasEnded(false), []);

  return (
    <AnimatePresence mode="wait">
      {/* Ready / Connecting — welcome masthead */}
      {!isConnected && !hasEnded && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
          isStarting={isStarting}
        />
      )}

      {/* Live session — custom Aarogya Saathi chat UI */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          className="fixed inset-0"
          supportsChatInput={appConfig.supportsChatInput}
        />
      )}

      {/* Call ended */}
      {!isConnected && hasEnded && (
        <MotionCallEndedView
          key="call-ended"
          {...VIEW_MOTION_PROPS}
          onRestart={handleStart}
          onHome={handleHome}
        />
      )}
    </AnimatePresence>
  );
}
