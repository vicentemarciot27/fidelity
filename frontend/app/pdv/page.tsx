import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { QrCode, Scan, Plus } from "lucide-react"

export default function PDVPage() {
  return (
    <div className="space-y-8">
      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5" />
              Resgatar Cupom
            </CardTitle>
            <CardDescription>Escaneie ou digite o código do cupom</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="coupon-code">Código do Cupom</Label>
              <div className="flex gap-2">
                <Input id="coupon-code" placeholder="Digite ou escaneie o código" />
                <Button size="icon" variant="outline">
                  <Scan className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <Button className="w-full">Resgatar Cupom</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Acumular Pontos
            </CardTitle>
            <CardDescription>Adicione pontos para o cliente</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="customer-id">ID do Cliente</Label>
              <Input id="customer-id" placeholder="Digite o ID do cliente" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="points">Pontos a Adicionar</Label>
              <Input id="points" type="number" placeholder="100" />
            </div>
            <Button className="w-full">Adicionar Pontos</Button>
          </CardContent>
        </Card>
      </div>

      {/* Placeholder Content */}
      <div className="grid md:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Transações Recentes</CardTitle>
            <CardDescription>Últimas atividades do PDV</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Em desenvolvimento: Lista das últimas transações realizadas neste PDV.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Estatísticas do Dia</CardTitle>
            <CardDescription>Resumo das atividades de hoje</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Em desenvolvimento: Estatísticas diárias de cupons resgatados e pontos distribuídos.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
