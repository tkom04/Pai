import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Orbit - Your Personal AI Command Center</title>
        <meta name="description" content="Orbit brings together your calendar, tasks, shopping lists, and smart home into one intelligent dashboard powered by AI." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}

