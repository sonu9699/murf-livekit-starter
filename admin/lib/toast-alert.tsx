import { type ReactNode } from 'react';
import { toast as sonnerToast } from 'sonner';
import { WarningIcon } from '@phosphor-icons/react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export interface ToastAlertProps {
  title: ReactNode;
  description?: ReactNode;
  /** `destructive` tints the alert red — use for hard failures like a denied mic. */
  variant?: 'default' | 'destructive';
  /** How long the toast stays up, in ms. */
  duration?: number;
}

/**
 * Shows a dismissible, styled toast using the shadcn `Alert` surface.
 * Shared by session-failure and microphone-permission handling so every
 * warning the user sees looks the same.
 */
export function toastAlert({
  title,
  description,
  variant = 'default',
  duration = 10_000,
}: ToastAlertProps) {
  return sonnerToast.custom(
    (id) => (
      <Alert
        variant={variant}
        onClick={() => sonnerToast.dismiss(id)}
        className="bg-accent w-full cursor-pointer md:w-[364px]"
      >
        <WarningIcon weight="bold" />
        <AlertTitle>{title}</AlertTitle>
        {description && <AlertDescription>{description}</AlertDescription>}
      </Alert>
    ),
    { duration }
  );
}
