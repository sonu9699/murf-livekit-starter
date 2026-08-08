import { Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
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
      <body className="overflow-x-hidden">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <header className="fixed top-0 left-0 z-50 flex w-full flex-row items-center justify-between p-4 md:p-6">
            <div className="flex items-center gap-2.5">
              <span className="bg-primary size-3 rounded-[3px]" aria-hidden />
              <span className="font-display text-lg leading-none font-light tracking-tight">
                {companyName}
              </span>
            </div>
            <span className="text-muted-foreground hidden font-mono text-[0.7rem] font-medium tracking-[0.2em] uppercase md:inline">
              Bharat ka voice health saathi
            </span>
          </header>

          {children}
          <div className="group fixed bottom-0 left-1/2 z-50 mb-[max(0.5rem,env(safe-area-inset-bottom))] -translate-x-1/2">
            <ThemeToggle className="translate-y-0 transition-transform delay-150 duration-300 md:translate-y-20 md:group-hover:translate-y-0" />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
