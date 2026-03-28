/**
 * Risk Management Page
 * Monitor and control trading risk
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, AlertTriangle, TrendingDown, AlertOctagon } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const RiskManagement: React.FC = () => {
  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Risk Management</h2>
          <p className="text-muted-foreground">
            Monitor and control your trading risk exposure
          </p>
        </div>
        <Button variant="destructive">
          <AlertOctagon className="mr-2 h-4 w-4" />
          Emergency Stop
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Account Equity</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$100,000</div>
            <p className="text-xs text-muted-foreground">Total account value</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily P&L</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">-$250</div>
            <Progress value={12.5} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">12.5% of daily limit</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Risk</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$500</div>
            <p className="text-xs text-muted-foreground">Current exposure</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Score</CardTitle>
            <Shield className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3/10</div>
            <p className="text-xs text-muted-foreground">Low risk</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="limits">Risk Limits</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Overview</CardTitle>
              <CardDescription>
                Current risk status and exposure
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Daily Loss Limit</span>
                  <span className="font-medium">$2,000</span>
                </div>
                <Progress value={12.5} />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Max Drawdown</span>
                  <span className="font-medium">10%</span>
                </div>
                <Progress value={2} />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Position Exposure</span>
                  <span className="font-medium">5%</span>
                </div>
                <Progress value={5} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="limits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Limits Configuration</CardTitle>
              <CardDescription>
                Set and manage your risk parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Max Position Size</span>
                  <span className="font-medium">5 contracts</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Max Daily Loss</span>
                  <span className="font-medium">$2,000</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Max Drawdown</span>
                  <span className="font-medium">10%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Stop Loss Required</span>
                  <span className="font-medium">Yes</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Alerts</CardTitle>
              <CardDescription>
                Active risk warnings and notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>No Active Alerts</AlertTitle>
                <AlertDescription>
                  All risk parameters are within acceptable limits.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Metrics</CardTitle>
              <CardDescription>
                Detailed risk analytics and statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Start trading to see risk metrics
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RiskManagement;