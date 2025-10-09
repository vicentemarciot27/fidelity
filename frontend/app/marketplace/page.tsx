import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Gift, Star, Clock } from "lucide-react"

export default function MarketplacePage() {
  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Seus Pontos</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,450</div>
            <p className="text-xs text-muted-foreground">+180 pontos este mês</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cupons Ativos</CardTitle>
            <Gift className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Válidos até o fim do mês</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nível</CardTitle>
            <Badge variant="secondary">Gold</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Gold</div>
            <p className="text-xs text-muted-foreground">550 pontos para Platinum</p>
          </CardContent>
        </Card>
      </div>

      {/* Placeholder Content */}
      <div className="grid md:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gift className="h-5 w-5" />
              Ofertas Disponíveis
            </CardTitle>
            <CardDescription>Resgate seus pontos por recompensas incríveis</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Em desenvolvimento: Lista de ofertas disponíveis para resgate com pontos.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Histórico de Transações
            </CardTitle>
            <CardDescription>Acompanhe seus ganhos e gastos de pontos</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Em desenvolvimento: Histórico detalhado de todas as transações de pontos.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
