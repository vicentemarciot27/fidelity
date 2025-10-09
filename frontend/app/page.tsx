import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ShoppingBag, Store, Settings, Users, TrendingUp, Shield } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"

export default function HomePage() {
  return (
    <MainLayout>
      <div className="bg-gradient-to-br from-muted/50 to-background">
        {/* Hero Section */}
        <section className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4">Sistema de Fidelidade</h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              Plataforma completa para gerenciamento de programas de fidelidade multi-tenant
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/auth/register">Começar Agora</Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/auth/login">Fazer Login</Link>
              </Button>
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto mb-16">
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="text-center">
                <ShoppingBag className="w-12 h-12 mx-auto mb-4 text-accent" />
                <CardTitle>Marketplace</CardTitle>
                <CardDescription>Interface para clientes navegarem ofertas e gerenciarem pontos</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild className="w-full">
                  <Link href="/marketplace">Acessar Marketplace</Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="text-center">
                <Store className="w-12 h-12 mx-auto mb-4 text-chart-1" />
                <CardTitle>PDV</CardTitle>
                <CardDescription>Sistema para pontos de venda gerenciarem cupons e pontos</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild className="w-full">
                  <Link href="/pdv">Acessar PDV</Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="text-center">
                <Settings className="w-12 h-12 mx-auto mb-4 text-chart-4" />
                <CardTitle>Admin</CardTitle>
                <CardDescription>Painel administrativo para gerenciar todo o sistema</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild className="w-full">
                  <Link href="/admin">Acessar Admin</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="bg-card">
          <div className="container mx-auto px-4 py-16">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Por que escolher nosso sistema?</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Recursos avançados para maximizar o engajamento dos clientes e o crescimento do seu negócio
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <Users className="w-16 h-16 mx-auto mb-4 text-accent" />
                <h3 className="text-xl font-semibold mb-2">Multi-tenant</h3>
                <p className="text-muted-foreground">
                  Suporte completo para múltiplas franquias e lojas em uma única plataforma
                </p>
              </div>

              <div className="text-center">
                <TrendingUp className="w-16 h-16 mx-auto mb-4 text-chart-1" />
                <h3 className="text-xl font-semibold mb-2">Analytics Avançado</h3>
                <p className="text-muted-foreground">
                  Relatórios detalhados e insights para otimizar seu programa de fidelidade
                </p>
              </div>

              <div className="text-center">
                <Shield className="w-16 h-16 mx-auto mb-4 text-chart-4" />
                <h3 className="text-xl font-semibold mb-2">Segurança</h3>
                <p className="text-muted-foreground">
                  Proteção avançada de dados e transações com criptografia de ponta
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </MainLayout>
  )
}
