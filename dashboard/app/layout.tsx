import Link from "next/link";
import "./globals.css";

export const metadata = { title: "Momentum Scanner" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <strong>Momentum Scanner</strong>
          <nav>
            <Link href="/">Alerts</Link>
            <Link href="/scoreboard">Scoreboard</Link>
            <Link href="/journal">Journal</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
