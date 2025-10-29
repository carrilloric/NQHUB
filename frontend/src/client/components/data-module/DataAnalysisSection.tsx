import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const analysisSections = [
  {
    value: "exploratory-data-analysis",
    title: "Exploratory Data Analysis",
    summary: "Investigate feature behavior and distributional properties before modeling.",
    bulletPoints: [
      {
        title: "Univariate analysis",
        detail: "Generate summary statistics, density plots, and extreme value detection for each feature.",
      },
      {
        title: "Bivariate relationships",
        detail: "Measure pairwise associations using scatter matrices and rank correlations.",
      },
      {
        title: "Correlation analysis",
        detail: "Build clustered heatmaps with Pearson and Spearman coefficients to spot multicollinearity.",
      },
      {
        title: "Distribution assessment",
        detail: "Run normality and stationarity checks to validate modeling assumptions.",
      },
    ],
  },
  {
    value: "unsupervised-learning-analysis",
    title: "Unsupervised Learning Analysis",
    summary: "Reveal latent structure across the feature space with clustering and dimensionality reduction.",
    bulletPoints: [
      {
        title: "K-means clustering",
        detail: "Evaluate compactness and separation metrics across configurable cluster counts.",
      },
      {
        title: "Principal Component Analysis (PCA)",
        detail: "Quantify variance explained and inspect component loadings for interpretability.",
      },
      {
        title: "Cluster interpretation",
        detail: "Surface centroid feature importance and sample representatives for each cluster.",
      },
    ],
  },
  {
    value: "linear-regression-modeling",
    title: "Linear Regression Modeling",
    summary: "Fit baseline predictive models and validate performance prior to advanced experimentation.",
    bulletPoints: [
      {
        title: "Simple linear regression",
        detail: "Benchmark single-factor response relationships with confidence interval reporting.",
      },
      {
        title: "Multiple linear regression",
        detail: "Run multivariate fits with regularization toggles for feature shrinkage and selection.",
      },
      {
        title: "Model diagnostics",
        detail: "Inspect residual plots, leverage scores, and heteroscedasticity tests.",
      },
      {
        title: "Interpretation and conclusions",
        detail: "Document coefficient insights, predictive lift, and production readiness notes.",
      },
    ],
  },
] as const;

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
] as const;

export const DataAnalysisSection = () => {
  return (
    <div className="flex h-full flex-col gap-8 overflow-hidden">
      <header className="space-y-3">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
          Data Analysis Report
        </p>
        <h2 className="text-3xl font-semibold text-foreground/90">
          Standardized exploratory, unsupervised, and regression workflows
        </h2>
        <p className="max-w-3xl text-sm text-muted-foreground/80">
          Use this workspace to document findings, compare modeling runs, and maintain auditable analytics
          procedures across exploratory research and production-ready baselines.
        </p>
      </header>

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

      <section className="rounded-3xl border border-border/40 bg-[radial-gradient(circle_at_top_left,_rgba(23,211,218,0.12),_transparent)] bg-[#0b1523] p-6 shadow-[0_20px_40px_rgba(0,0,0,0.45)]">
        <Accordion type="single" collapsible defaultValue="exploratory-data-analysis">
          {analysisSections.map((section) => (
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
      </section>
    </div>
  );
};
