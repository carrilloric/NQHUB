import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { AssistantPanelSidebar } from "@/assistant";
import { useI18n } from "@/state/app";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

type AnalysisTab = "eda" | "unsupervised" | "regression";

// Analysis sections data
const edaSections = [
  {
    value: "univariate",
    title: "Univariate Analysis",
    summary: "Generate summary statistics, density plots, and extreme value detection for each feature.",
    bulletPoints: [
      {
        title: "Summary statistics",
        detail: "Mean, median, mode, standard deviation, and quartiles for all numeric features.",
      },
      {
        title: "Density plots",
        detail: "Visualize distribution shape with histograms and kernel density estimates.",
      },
      {
        title: "Extreme values",
        detail: "Detect outliers using IQR method and Z-score thresholds.",
      },
    ],
  },
  {
    value: "bivariate",
    title: "Bivariate Relationships",
    summary: "Measure pairwise associations using scatter matrices and rank correlations.",
    bulletPoints: [
      {
        title: "Scatter plots",
        detail: "Visualize relationships between pairs of continuous variables.",
      },
      {
        title: "Correlation coefficients",
        detail: "Calculate Pearson and Spearman correlation for linear and monotonic relationships.",
      },
    ],
  },
  {
    value: "correlation",
    title: "Correlation Analysis",
    summary: "Build clustered heatmaps with Pearson and Spearman coefficients to spot multicollinearity.",
    bulletPoints: [
      {
        title: "Correlation heatmap",
        detail: "Color-coded matrix showing correlation strength between all feature pairs.",
      },
      {
        title: "Multicollinearity detection",
        detail: "Identify highly correlated features that may cause model instability.",
      },
    ],
  },
  {
    value: "distribution",
    title: "Distribution Assessment",
    summary: "Run normality and stationarity checks to validate modeling assumptions.",
    bulletPoints: [
      {
        title: "Normality tests",
        detail: "Shapiro-Wilk and Anderson-Darling tests for normal distribution.",
      },
      {
        title: "Stationarity tests",
        detail: "Augmented Dickey-Fuller test for time series data.",
      },
    ],
  },
];

const unsupervisedSections = [
  {
    value: "kmeans",
    title: "K-means Clustering",
    summary: "Evaluate compactness and separation metrics across configurable cluster counts.",
    bulletPoints: [
      {
        title: "Elbow method",
        detail: "Determine optimal number of clusters using within-cluster sum of squares.",
      },
      {
        title: "Silhouette analysis",
        detail: "Measure cluster quality with silhouette coefficients.",
      },
      {
        title: "Cluster profiling",
        detail: "Analyze feature means and distributions within each cluster.",
      },
    ],
  },
  {
    value: "pca",
    title: "Principal Component Analysis (PCA)",
    summary: "Quantify variance explained and inspect component loadings for interpretability.",
    bulletPoints: [
      {
        title: "Variance explained",
        detail: "Cumulative variance plot to determine number of components to retain.",
      },
      {
        title: "Component loadings",
        detail: "Feature contributions to each principal component.",
      },
      {
        title: "Dimensionality reduction",
        detail: "Project high-dimensional data into 2D/3D for visualization.",
      },
    ],
  },
  {
    value: "interpretation",
    title: "Cluster Interpretation",
    summary: "Surface centroid feature importance and sample representatives for each cluster.",
    bulletPoints: [
      {
        title: "Centroid analysis",
        detail: "Examine feature values at cluster centers.",
      },
      {
        title: "Representative samples",
        detail: "Identify most typical examples from each cluster.",
      },
    ],
  },
];

const regressionSections = [
  {
    value: "simple",
    title: "Simple Linear Regression",
    summary: "Benchmark single-factor response relationships with confidence interval reporting.",
    bulletPoints: [
      {
        title: "Univariate models",
        detail: "Fit y = mx + b for each feature against target variable.",
      },
      {
        title: "Confidence intervals",
        detail: "95% confidence bands for slope and intercept estimates.",
      },
      {
        title: "R-squared metrics",
        detail: "Coefficient of determination to assess goodness of fit.",
      },
    ],
  },
  {
    value: "multiple",
    title: "Multiple Linear Regression",
    summary: "Run multivariate fits with regularization toggles for feature shrinkage and selection.",
    bulletPoints: [
      {
        title: "Multivariate models",
        detail: "Fit models with multiple predictors simultaneously.",
      },
      {
        title: "Regularization",
        detail: "Ridge (L2) and Lasso (L1) regularization for feature selection.",
      },
      {
        title: "Cross-validation",
        detail: "K-fold CV to prevent overfitting and tune hyperparameters.",
      },
    ],
  },
  {
    value: "diagnostics",
    title: "Model Diagnostics",
    summary: "Inspect residual plots, leverage scores, and heteroscedasticity tests.",
    bulletPoints: [
      {
        title: "Residual analysis",
        detail: "Plot residuals vs. fitted values to check model assumptions.",
      },
      {
        title: "Leverage and influence",
        detail: "Identify high-leverage points and influential observations.",
      },
      {
        title: "Heteroscedasticity tests",
        detail: "Breusch-Pagan and White tests for constant variance.",
      },
    ],
  },
  {
    value: "conclusions",
    title: "Interpretation and Conclusions",
    summary: "Document coefficient insights, predictive lift, and production readiness notes.",
    bulletPoints: [
      {
        title: "Coefficient interpretation",
        detail: "Understand the effect size and direction of each predictor.",
      },
      {
        title: "Predictive performance",
        detail: "RMSE, MAE, and R² on held-out test set.",
      },
      {
        title: "Production readiness",
        detail: "Assess model stability, interpretability, and deployment considerations.",
      },
    ],
  },
];

const summaryHighlights = [
  {
    label: "Quality checks",
    value: "24",
    description: "Automated validations executed per dataset prior to downstream processing.",
  },
  {
    label: "Feature coverage",
    value: "92%",
    description: "Percentage of engineered signals passing completeness thresholds.",
  },
  {
    label: "Model iterations",
    value: "12",
    description: "Regression experiments preserved for comparison in the reporting workspace.",
  },
];

export const StatisticalAnalysis: React.FC = () => {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<AnalysisTab>("eda");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="pl-16 md:pl-64 flex min-h-screen items-start bg-[radial-gradient(circle_at_top_left,_rgba(23,211,218,0.12),_transparent)]">
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-auto px-4 py-8 md:px-10">
            <div className="flex flex-col gap-6">
              <div className="space-y-3">
                <h1 className="text-5xl font-extrabold tracking-tight text-foreground">
                  {t("nav.statisticalAnalysis")}
                </h1>
                <p className="text-sm text-muted-foreground/80">
                  Standardized exploratory, unsupervised, and regression workflows for NQ futures data
                </p>
              </div>

              {/* Summary Highlights */}
              <section className="grid gap-4 md:grid-cols-3">
                {summaryHighlights.map((highlight) => (
                  <div
                    key={highlight.label}
                    className="rounded-2xl border border-border/40 bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.16),_transparent)] bg-[#101a2c] p-5 shadow-[0_16px_32px_rgba(0,0,0,0.45)]"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-muted-foreground/60">
                      {highlight.label}
                    </p>
                    <p className="mt-3 text-3xl font-bold text-primary">{highlight.value}</p>
                    <p className="mt-2 text-sm text-muted-foreground/75">{highlight.description}</p>
                  </div>
                ))}
              </section>

              {/* Tabs Section */}
              <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-[#121b2d] via-[#0b1523] to-[#090f19] shadow-[0_24px_48px_rgba(0,0,0,0.55)]">
                <Tabs
                  value={activeTab}
                  onValueChange={(value) => setActiveTab(value as AnalysisTab)}
                  className="flex h-full flex-col"
                >
                  <TabsList className="grid w-full grid-cols-3 px-4">
                    <TabsTrigger value="eda">📊 Exploratory Data Analysis</TabsTrigger>
                    <TabsTrigger value="unsupervised">🧬 Unsupervised Learning</TabsTrigger>
                    <TabsTrigger value="regression">📈 Linear Regression</TabsTrigger>
                  </TabsList>

                  <div className="flex-1 overflow-hidden">
                    {/* EDA Tab */}
                    <TabsContent
                      value="eda"
                      className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6"
                    >
                      <div className="space-y-4">
                        <header className="space-y-2">
                          <h2 className="text-2xl font-semibold text-foreground/90">
                            Exploratory Data Analysis
                          </h2>
                          <p className="text-sm text-muted-foreground/80">
                            Investigate feature behavior and distributional properties before modeling
                          </p>
                        </header>

                        <Accordion type="single" collapsible defaultValue="univariate">
                          {edaSections.map((section) => (
                            <AccordionItem key={section.value} value={section.value} className="border-border/30">
                              <AccordionTrigger className="text-left text-lg font-semibold text-foreground/90">
                                <div className="flex flex-col gap-1 text-left">
                                  <span className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                                    {section.title}
                                  </span>
                                  <span className="text-base font-normal text-muted-foreground/80">
                                    {section.summary}
                                  </span>
                                </div>
                              </AccordionTrigger>
                              <AccordionContent className="grid gap-4 pt-4 md:grid-cols-2">
                                {section.bulletPoints.map((point) => (
                                  <div
                                    key={point.title}
                                    className="rounded-2xl border border-border/40 bg-[#111c2f] p-4 shadow-[0_12px_24px_rgba(0,0,0,0.35)]"
                                  >
                                    <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-primary/80">
                                      {point.title}
                                    </h4>
                                    <p className="mt-3 text-sm text-muted-foreground/80">{point.detail}</p>
                                  </div>
                                ))}
                              </AccordionContent>
                            </AccordionItem>
                          ))}
                        </Accordion>
                      </div>
                    </TabsContent>

                    {/* Unsupervised Learning Tab */}
                    <TabsContent
                      value="unsupervised"
                      className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6"
                    >
                      <div className="space-y-4">
                        <header className="space-y-2">
                          <h2 className="text-2xl font-semibold text-foreground/90">
                            Unsupervised Learning Analysis
                          </h2>
                          <p className="text-sm text-muted-foreground/80">
                            Reveal latent structure across the feature space with clustering and dimensionality reduction
                          </p>
                        </header>

                        <Accordion type="single" collapsible defaultValue="kmeans">
                          {unsupervisedSections.map((section) => (
                            <AccordionItem key={section.value} value={section.value} className="border-border/30">
                              <AccordionTrigger className="text-left text-lg font-semibold text-foreground/90">
                                <div className="flex flex-col gap-1 text-left">
                                  <span className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                                    {section.title}
                                  </span>
                                  <span className="text-base font-normal text-muted-foreground/80">
                                    {section.summary}
                                  </span>
                                </div>
                              </AccordionTrigger>
                              <AccordionContent className="grid gap-4 pt-4 md:grid-cols-2">
                                {section.bulletPoints.map((point) => (
                                  <div
                                    key={point.title}
                                    className="rounded-2xl border border-border/40 bg-[#111c2f] p-4 shadow-[0_12px_24px_rgba(0,0,0,0.35)]"
                                  >
                                    <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-primary/80">
                                      {point.title}
                                    </h4>
                                    <p className="mt-3 text-sm text-muted-foreground/80">{point.detail}</p>
                                  </div>
                                ))}
                              </AccordionContent>
                            </AccordionItem>
                          ))}
                        </Accordion>
                      </div>
                    </TabsContent>

                    {/* Linear Regression Tab */}
                    <TabsContent
                      value="regression"
                      className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6"
                    >
                      <div className="space-y-4">
                        <header className="space-y-2">
                          <h2 className="text-2xl font-semibold text-foreground/90">
                            Linear Regression Modeling
                          </h2>
                          <p className="text-sm text-muted-foreground/80">
                            Fit baseline predictive models and validate performance prior to advanced experimentation
                          </p>
                        </header>

                        <Accordion type="single" collapsible defaultValue="simple">
                          {regressionSections.map((section) => (
                            <AccordionItem key={section.value} value={section.value} className="border-border/30">
                              <AccordionTrigger className="text-left text-lg font-semibold text-foreground/90">
                                <div className="flex flex-col gap-1 text-left">
                                  <span className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
                                    {section.title}
                                  </span>
                                  <span className="text-base font-normal text-muted-foreground/80">
                                    {section.summary}
                                  </span>
                                </div>
                              </AccordionTrigger>
                              <AccordionContent className="grid gap-4 pt-4 md:grid-cols-2">
                                {section.bulletPoints.map((point) => (
                                  <div
                                    key={point.title}
                                    className="rounded-2xl border border-border/40 bg-[#111c2f] p-4 shadow-[0_12px_24px_rgba(0,0,0,0.35)]"
                                  >
                                    <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-primary/80">
                                      {point.title}
                                    </h4>
                                    <p className="mt-3 text-sm text-muted-foreground/80">{point.detail}</p>
                                  </div>
                                ))}
                              </AccordionContent>
                            </AccordionItem>
                          ))}
                        </Accordion>
                      </div>
                    </TabsContent>
                  </div>
                </Tabs>
              </div>
            </div>
          </div>
        </div>
        <AssistantPanelSidebar />
      </main>
    </div>
  );
};

export default StatisticalAnalysis;
