import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bot, FlaskConical, TrendingUp } from "lucide-react";
import { useAuth, useI18n } from "@/state/app";
import { useNavigate } from "react-router-dom";

const ModuleCard: React.FC<{ icon: React.ReactNode; title: string; description: string; disabled?: boolean; onLaunch: () => void; }> = ({ icon, title, description, disabled, onLaunch }) => {
  return (
    <Card className="group hover:shadow-xl transition-all border-border/60 bg-card/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-3 text-xl">{icon} {title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button disabled={disabled} onClick={onLaunch} className="mt-2">
          {disabled ? "Locked" : "Launch"}
        </Button>
      </CardContent>
    </Card>
  );
};

export const ModuleLauncher: React.FC = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const nav = useNavigate();

  const canBacktest = user?.role === "trader" || user?.role === "analystSenior" || user?.role === "analystJunior" || user?.role === "admin";
  const canBot = user?.role === "trader" || user?.role === "admin";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <ModuleCard
        icon={<TrendingUp className="text-primary" />}
        title={t("dashboard.moduleData")}
        description={t("dashboard.dataDescription")}
        onLaunch={() => nav("/data")}
      />
      <ModuleCard
        icon={<FlaskConical className="text-primary" />}
        title={t("dashboard.moduleBacktest")}
        description={t("dashboard.backtestDescription")}
        disabled={!canBacktest}
        onLaunch={() => nav("/backtesting")}
      />
      <ModuleCard
        icon={<Bot className="text-primary" />}
        title={t("dashboard.moduleBot")}
        description={t("dashboard.botDescription")}
        disabled={!canBot}
        onLaunch={() => nav("/bot")}
      />
    </div>
  );
};
