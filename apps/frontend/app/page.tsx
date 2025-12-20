import { ChatInterface } from '@/components/chat-interface'
import { createClient } from '@/lib/supabase/server'

export default async function Home() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getClaims()
  const isAuthenticated = !!data?.claims

  return (
    <>
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl opacity-50 animate-pulse" />
        <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl opacity-50 animate-pulse [animation-delay:2s]" />
      </div>

      <ChatInterface isAuthenticated={isAuthenticated} />
    </>
  )
}
