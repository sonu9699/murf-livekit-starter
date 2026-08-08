'use client';

import { memo } from 'react';
import remarkGfm from 'remark-gfm';
import { MarkdownTextPrimitive } from '@assistant-ui/react-markdown';
import { cn } from '@/lib/shadcn/utils';

/**
 * Minimal markdown renderer for assistant-ui message text parts. The agent
 * replies in plain Devanagari sentences, so we only need clean paragraph
 * spacing — no code blocks, tables, or copy buttons.
 */
export const MarkdownText = memo(function MarkdownText() {
  return (
    <MarkdownTextPrimitive
      remarkPlugins={[remarkGfm]}
      className={cn(
        'aui-md',
        '[&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        '[&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-0 [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5'
      )}
    />
  );
});
