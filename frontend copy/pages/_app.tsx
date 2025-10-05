import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  // Bypass authentication for testing
  return (
    <>
      <Head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <title>Personal AI Assistant</title>
      </Head>
      <Component {...pageProps} />
    </>
  )
}
