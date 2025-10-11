import React from "react";
import { useLocation } from "react-router-dom";

export const Placeholder: React.FC<{ title?: string; description?: string }> = ({ title, description }) => {
  const loc = useLocation();
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-2">{title || "Coming soon"}</h1>
      <p className="text-muted-foreground">{description || `This page (${loc.pathname}) is a placeholder. Ask to generate this page when you're ready.`}</p>
    </div>
  );
};
