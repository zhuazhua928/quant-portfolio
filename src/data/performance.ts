// Placeholder performance data — replace with your actual data

function generateEquityCurve() {
  const data: { date: string; equity: number; dailyReturn: number }[] = [];
  let equity = 1000000;
  const startDate = new Date("2023-01-01");

  for (let i = 0; i < 730; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    const dailyReturn =
      (Math.random() - 0.48) * 0.012 +
      Math.sin(i / 60) * 0.002;
    equity *= 1 + dailyReturn;

    data.push({
      date: date.toISOString().split("T")[0],
      equity: Math.round(equity),
      dailyReturn: parseFloat((dailyReturn * 100).toFixed(3)),
    });
  }

  return data;
}

function computeRollingMetrics(
  data: { date: string; dailyReturn: number }[],
  window: number
) {
  const result = [];

  for (let i = window; i < data.length; i++) {
    const slice = data.slice(i - window, i);
    const returns = slice.map((d) => d.dailyReturn / 100);
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance =
      returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length;
    const vol = Math.sqrt(variance) * Math.sqrt(252);
    const annReturn = mean * 252;
    const sharpe = vol > 0 ? annReturn / vol : 0;

    result.push({
      date: data[i].date,
      rollingSharpe: parseFloat(sharpe.toFixed(2)),
      rollingVol: parseFloat((vol * 100).toFixed(2)),
    });
  }

  return result;
}

function generateExposure(data: { date: string }[]) {
  return data.map((d, i) => ({
    date: d.date,
    longExposure: parseFloat(
      (60 + Math.sin(i / 40) * 15 + Math.random() * 5).toFixed(1)
    ),
    shortExposure: parseFloat(
      (25 + Math.cos(i / 35) * 10 + Math.random() * 5).toFixed(1)
    ),
    netExposure: parseFloat(
      (35 + Math.sin(i / 40) * 15 - Math.cos(i / 35) * 10).toFixed(1)
    ),
  }));
}

const equityData = generateEquityCurve();

// Compute proper drawdown series from running peak
let peak = equityData[0].equity;
const drawdownData = equityData.map((d) => {
  if (d.equity > peak) peak = d.equity;
  const dd = ((d.equity - peak) / peak) * 100;
  return { date: d.date, drawdown: parseFloat(dd.toFixed(2)) };
});

export const performanceData = {
  equity: equityData.map((d) => ({ date: d.date, equity: d.equity })),
  drawdown: drawdownData,
  rolling: computeRollingMetrics(equityData, 63),
  exposure: generateExposure(equityData),
};

export const summaryMetrics = {
  totalReturn: "Placeholder",
  annualizedReturn: "Placeholder",
  annualizedVol: "Placeholder",
  sharpeRatio: "Placeholder",
  sortinoRatio: "Placeholder",
  maxDrawdown: "Placeholder",
  calmarRatio: "Placeholder",
  winRate: "Placeholder",
  avgWin: "Placeholder",
  avgLoss: "Placeholder",
  profitFactor: "Placeholder",
  avgHoldingPeriod: "Placeholder",
};
