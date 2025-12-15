import { PromptInterface } from '@/components/prompt-interface'
import { createClient } from '@/lib/supabase/server'

export default async function Home() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getClaims()
  const isAuthenticated = !!data?.claims

  return (
    <main className="min-h-screen py-12 px-4">
      <PromptInterface isAuthenticated={isAuthenticated} />
    </main>
  )
}
