export interface Project {
  slug: string;
  title: string;
  subtitle: string;
  category: string;
  period: string;
  tags: string[];
  summary: string;
  sections: {
    title: string;
    content: string;
  }[];
  highlights: string[];
}

export const projects: Project[] = [
  {
    slug: "systematic-momentum-strategy",
    title: "Cross-Asset Momentum Strategy",
    subtitle: "Systematic trend-following framework across futures markets",
    category: "Systematic Trading",
    period: "2023 – Present",
    tags: ["Futures", "Momentum", "Risk Parity", "Python"],
    summary:
      "Designed and implemented a systematic momentum strategy operating across equity index, fixed income, and commodity futures. The framework combines multiple lookback horizons with volatility-scaled position sizing to capture persistent trends while managing tail risk.",
    sections: [
      {
        title: "Research Approach",
        content:
          "The strategy was developed through a structured research process: hypothesis formulation grounded in behavioral finance literature, followed by rigorous out-of-sample testing with conservative transaction cost assumptions. Signal construction uses a blend of time-series momentum signals across multiple horizons, avoiding overfitting to any single parameter set.",
      },
      {
        title: "Portfolio Construction",
        content:
          "Positions are sized using an inverse-volatility weighting scheme with an overall portfolio risk target. Correlation-aware allocation ensures diversification benefits are realized across asset classes. The framework includes dynamic leverage adjustment based on realized portfolio volatility relative to the target.",
      },
      {
        title: "Execution & Infrastructure",
        content:
          "Built on a modular Python-based backtesting and live-trading infrastructure. The system handles signal generation, position sizing, order management, and reconciliation. Execution is managed through a scheduling layer that sequences trades to minimize market impact.",
      },
      {
        title: "Risk Management",
        content:
          "Integrated stop-loss mechanisms at both the instrument and portfolio level. The strategy includes drawdown-based deleveraging rules and exposure caps per sector. All risk parameters were calibrated using historical stress periods rather than optimized in-sample.",
      },
    ],
    highlights: [
      "Multi-asset class coverage: equity indices, rates, commodities",
      "Robust out-of-sample validation with walk-forward analysis",
      "Volatility-targeting framework with dynamic position sizing",
      "Fully automated signal generation and order management pipeline",
    ],
  },
  {
    slug: "event-monitoring-system",
    title: "Event & News Monitoring System",
    subtitle: "Real-time alternative data pipeline for systematic signal generation",
    category: "Alternative Data",
    period: "2024 – Present",
    tags: ["NLP", "Event-Driven", "Data Engineering", "Python", "AWS"],
    summary:
      "Built a scalable event monitoring platform that ingests, processes, and scores news and corporate events in near real-time. The system identifies material events — earnings surprises, regulatory actions, management changes — and translates them into structured signals for downstream consumption by trading models.",
    sections: [
      {
        title: "Data Architecture",
        content:
          "Designed a streaming data pipeline that ingests from multiple news and filing sources. Raw text is processed through a series of NLP stages: entity extraction, event classification, and sentiment scoring. The architecture is built for horizontal scalability and processes thousands of documents per hour with sub-minute latency.",
      },
      {
        title: "Signal Construction",
        content:
          "Events are mapped to a proprietary taxonomy that distinguishes between different materiality tiers. Signals are generated based on event type, historical base rates of similar events, and the magnitude of deviation from market expectations. Signal decay profiles are modeled to account for information diffusion speed across different event categories.",
      },
      {
        title: "Integration & Monitoring",
        content:
          "The platform exposes signals via a REST API and publishes to a message queue for real-time consumption. A monitoring dashboard tracks data freshness, processing latency, and signal quality metrics. Automated alerts flag anomalies in data volume or processing failures.",
      },
      {
        title: "Validation Framework",
        content:
          "Signal efficacy is evaluated using event-study methodology with proper controls for sector, market cap, and contemporaneous market moves. The validation framework runs continuously to detect signal degradation and generates periodic reports on hit rates and information coefficients across different event categories.",
      },
    ],
    highlights: [
      "Near real-time processing with sub-minute latency targets",
      "Structured event taxonomy with materiality classification",
      "Event-study validation framework with proper statistical controls",
      "Scalable cloud-native architecture on AWS",
    ],
  },
  {
    slug: "risk-overlay-framework",
    title: "Portfolio Risk Overlay Framework",
    subtitle: "Systematic risk monitoring and dynamic hedging toolkit",
    category: "Risk Management",
    period: "2023 – Present",
    tags: ["Risk", "Greeks", "VaR", "Python", "Real-Time"],
    summary:
      "Developed a comprehensive risk overlay system that provides real-time portfolio risk decomposition, scenario analysis, and automated hedging recommendations. The framework integrates with existing trading systems to enforce risk limits and generate alerts when exposures breach predefined thresholds.",
    sections: [
      {
        title: "Risk Decomposition",
        content:
          "The framework decomposes portfolio risk across multiple dimensions: factor exposures (market, sector, style), Greeks for options positions, and liquidity risk scoring. Risk is measured using both parametric and historical simulation approaches, with stress testing against a curated set of historical and hypothetical scenarios.",
      },
      {
        title: "Monitoring & Alerts",
        content:
          "A real-time dashboard displays current exposures, P&L attribution, and risk limit utilization. The alert system monitors a configurable set of risk metrics and triggers notifications when thresholds are approached or breached. All alerts include contextual information to support rapid decision-making.",
      },
      {
        title: "Hedging Engine",
        content:
          "The hedging module recommends optimal hedge portfolios using a cost-aware optimization framework. It considers transaction costs, margin requirements, and hedge effectiveness when proposing trades. Recommendations are generated both on a scheduled basis and in response to threshold-breaching events.",
      },
      {
        title: "Reporting & Attribution",
        content:
          "Automated daily and weekly risk reports provide performance attribution at the strategy, asset class, and factor level. The reporting module tracks how risk budgets are consumed over time and highlights concentration risks. All reports are generated in standardized formats suitable for internal review and compliance documentation.",
      },
    ],
    highlights: [
      "Multi-dimensional risk decomposition: factor, Greek, liquidity",
      "Real-time monitoring with configurable alert thresholds",
      "Cost-aware hedge optimization engine",
      "Automated compliance-ready reporting and attribution",
    ],
  },
];
