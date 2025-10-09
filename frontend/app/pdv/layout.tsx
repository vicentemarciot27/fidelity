import type React from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { AuthGuard } from "@/components/auth/auth-guard"

export default function PDVLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground">PDV - Ponto de Venda</h1>
            <p className="text-muted-foreground">Gerencie cupons e pontos dos clientes</p>
          </div>
          {children}
        </div>
      </MainLayout>
    </AuthGuard>
  )
}
