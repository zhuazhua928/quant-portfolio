export const resumeData = {
  name: "Yuheng (Paul) Yan",
  title: "Quantitative Researcher & Systematic Trader",
  email: "yyan75@jh.edu",
  phone: "+1 (410) 805-9842",
  location: "Baltimore, MD",
  links: {
    github: "https://github.com/yourusername",
    linkedin: "https://linkedin.com/in/yourusername",
  },
  education: [
    {
      degree: "MSE in Financial Mathematics",
      institution: "Johns Hopkins University",
      detail: "GPA: 3.8 / 4.0",
      period: "Sept 2024 – May 2026",
      bullets: [
        "Core Courses: Stochastic Process; Machine Learning; Investment Science; Advanced Statistical Theory; Advanced Equity Derivatives; Time Series Analysis; Interest Rate and Credit Derivatives; Commodity Markets; Mathematical Game Theory; Introduction to Data Science; Machine Learning in Finance",
      ],
    },
    {
      degree: "BS in Applied Mathematics",
      institution: "China University of Mining and Technology",
      detail: "Rank: 3 / 37",
      period: "Sept 2020 – June 2024",
      bullets: [],
    },
  ],
  experience: [
    {
      role: "Quantitative Research Intern → Tech Lead (CTO-level ownership)",
      firm: "SNTIMNT.AI",
      location: "Lake Mary, FL",
      period: "July 2025 – Present",
      bullets: [
        "Managed a 5-person quant team; owning an end-to-end trading system and reporting directly to CEO.",
        "Built the research→execution pipeline (data → signal → risk → backtest → paper/live) with robust monitoring under real-world constraints.",
        "Developed RL-based crypto strategies achieving Sharpe 1.95 and +85.3% out-of-sample return; improved generalization via reward/risk shaping and training stability.",
        "Directed NLP-driven sentiment analysis on crypto news and social media from different data sources, integrating signals to strengthen alpha generation.",
        "Designed investor-facing performance dashboard (PnL, exposure, drawdown, turnover) and collaborated with marketing to refine website messaging and product Q&A.",
        "Supported CEO in fundraising workflows by translating strategy/system capabilities into clear narratives, metrics, and diligence-ready materials.",
        "Validated internally developed strategies with personal capital, achieving a 100% return (2k → 4k) over two months.",
      ],
    },
    {
      role: "Quantitative Researcher Intern",
      firm: "Hangzhou Heixi Asset Management",
      location: "Hangzhou, China",
      period: "June 2023 – Dec 2023",
      bullets: [
        "Engineered high-frequency features from Level II order book data—including order flow imbalance and volume clustering—to uncover microstructure-driven alpha signals.",
        "Applied LSTM model to high-frequency order book data, enhancing signal extraction and predictability precision.",
      ],
    },
  ],
  research: [
    {
      title:
        "Identifying and Quantifying Financial Bubbles with the Hyped Log-Periodic Power Law Model",
      detail:
        "Co-First Author | Supervisor: Prof. Helyette Geman | Preprint: arxiv.org/abs/2510.10878 | Presented at The 21st Quantitative Finance Conference 2025, Italy; Upcoming Presentation at QuantMinds International 2025, London.",
      bullets: [
        "Co-developed a unified bubble detection framework integrating LPPL residual dynamics with NLP-based Hype Index and sentiment scores, leveraging behavioral finance to quantify overbought and oversold phenomena.",
        "Designed a dual-stream Transformer to jointly process stock-level and market-level signals, achieving MSE = 0.087 and Pearson correlation 0.625 in Bubble Index prediction.",
        "Implemented systematic trading strategies; delivered 34.1% average annualized return and Sharpe 1.13, with best cases exceeding 100% annualized return (Sharpe >3) in backtests for US market.",
      ],
    },
    {
      title: "Systematic Arbitrage & Factor Structure Analysis",
      detail:
        "Research Assistant, Carey Business School, Johns Hopkins University, Jan 2025 – July 2025",
      bullets: [
        "Replicated and extended a PPCA-based equity arbitrage framework from academic literature, constructing long–short portfolios; improved benchmark results by raising Sharpe from 0.7 to 1.6, annualized return from 18% to 23% and reducing max drawdown from 23% to 14%.",
        "Applied LASSO regression to high-frequency market microstructure features, isolating predictive signals while reducing dimensionality under real-time constraints.",
        "Benchmarked machine learning forecasts of quarterly P/E ratios; achieved MSE = 0.084.",
      ],
    },
  ],
  teaching: [
    {
      role: "Teaching Assistant, Empirical Finance",
      institution: "Johns Hopkins University",
      period: "Mar 2025 – July 2025",
      bullets: [
        "Guided students in building machine-learning pipelines for high-frequency trading using live tick data.",
        "Introduced NLP-based sentiment models (FinBERT/Vader) for portfolio optimization tasks.",
      ],
    },
    {
      role: "Teaching Assistant, Crypto and Blockchains",
      institution: "Johns Hopkins University",
      period: "Jan 2026 – Mar 2026",
      bullets: [
        "Supported crypto trading labs—on-chain flow auditing, stat-arb, RL trading, and AMM microstructure/slippage—helping students translate market microstructure + blockchain data into executable strategies.",
      ],
    },
  ],
  skills: {
    "Languages & Tools": [
      "Python",
      "C++",
      "SQL",
      "Microsoft (VBS)",
      "MATLAB",
      "R",
      "Linux",
    ],
    "ML & AI": [
      "PyTorch",
      "TensorFlow",
      "scikit-learn",
      "Machine Learning",
      "Deep Learning",
      "Reinforcement Learning",
      "NLP",
    ],
    "Platforms & Data": [
      "AWS Cloud",
      "Bloomberg Terminal",
      "LSEG Workspace",
      "DerivaGem",
    ],
  },
};
