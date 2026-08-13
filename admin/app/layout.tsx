import { Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
import Link from 'next/link';
import { ThemeProvider } from '@/components/app/theme-provider';
import { ThemeToggle } from '@/components/app/theme-toggle';
import { cn } from '@/lib/shadcn/utils';
import { getAppConfig, getStyles } from '@/lib/utils';
import '@/styles/globals.css';

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

const commitMono = localFont({
  display: 'swap',
  variable: '--font-commit-mono',
  src: [
    {
      path: '../fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);
  const styles = getStyles(appConfig);
  const { pageTitle, pageDescription, companyName } = appConfig;

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        publicSans.variable,
        commitMono.variable,
        'scroll-smooth font-sans antialiased'
      )}
    >
      <head>
        {styles && <style>{styles}</style>}
        <title>{pageTitle}</title>
        <meta name="description" content={pageDescription} />
      </head>
      <body className="overflow-x-hidden" suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <header className="fixed top-0 left-0 z-50 flex w-full flex-row items-center justify-end p-4 md:p-6">
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground hidden font-mono text-[0.7rem] font-medium tracking-[0.2em] uppercase md:inline">
                Aarogya Saathi - Admin Portal
              </span>
              <Link
                href="/escalations"
                className="text-muted-foreground hover:text-foreground border-border/80 hover:bg-primary/10 rounded-full border px-3.5 py-1 font-mono text-[0.7rem] font-medium tracking-[0.1em] uppercase transition-colors"
              >
                Escalations
              </Link>
              <Link
                href="/analytics"
                className="text-muted-foreground hover:text-foreground border-border/80 hover:bg-primary/10 rounded-full border px-3.5 py-1 font-mono text-[0.7rem] font-medium tracking-[0.1em] uppercase transition-colors"
              >
                Analytics
              </Link>
              <ThemeToggle className="w-auto" />
            </div>
          </header>

          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
