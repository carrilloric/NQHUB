/**
 * Features Engineering Page
 * Manage indicators and feature sets for trading strategies
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Plus, Calculator, Library } from 'lucide-react';

const Features: React.FC = () => {
  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Feature Engineering</h2>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Feature Set
        </Button>
      </div>

      <Tabs defaultValue="indicators" className="space-y-4">
        <TabsList>
          <TabsTrigger value="indicators">Indicators</TabsTrigger>
          <TabsTrigger value="features">Feature Sets</TabsTrigger>
          <TabsTrigger value="calculations">Calculations</TabsTrigger>
        </TabsList>

        <TabsContent value="indicators" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-4 w-4" />
                  Momentum
                </CardTitle>
                <CardDescription>RSI, MACD, Stochastic</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  5 indicators available
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-4 w-4" />
                  Trend
                </CardTitle>
                <CardDescription>SMA, EMA, ADX</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  7 indicators available
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-4 w-4" />
                  Volatility
                </CardTitle>
                <CardDescription>Bollinger Bands, ATR</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  4 indicators available
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="features" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Library className="h-4 w-4" />
                Saved Feature Sets
              </CardTitle>
              <CardDescription>
                Pre-configured indicator combinations for strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                No feature sets created yet
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calculations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Calculate Indicators</CardTitle>
              <CardDescription>
                Run indicator calculations on historical data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Select indicators and timeframe to calculate
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Features;