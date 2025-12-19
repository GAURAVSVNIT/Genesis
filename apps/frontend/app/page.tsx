import { ChatInterface } from '@/components/chat-interface'
import { createClient } from '@/lib/supabase/server'

export default async function Home() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getClaims()
  const isAuthenticated = !!data?.claims

  return (
    <main className="min-h-screen py-12 px-4">
      <ChatInterface isAuthenticated={isAuthenticated} />
    </main>
  )
}
