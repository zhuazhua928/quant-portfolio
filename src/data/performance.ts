// Performance data based on actual YTD results (Jan 1 – Mar 9, 2026)

function generateEquityCurve() {
  // Waypoints (cumulative return %) approximating the live equity shape:
  // Flat early Jan → sharp rally mid-Feb → pullback → recovery to ~+19.79%
  const waypoints: [number, number][] = [
    [0, 0],
    [5, -1.2],
    [10, 0.5],
    [15, 2.1],
    [20, 5.8],
    [25, 14.2],
    [30, 28.5],
    [33, 38.0],
    [35, 41.5],
    [37, 36.2],
    [39, 30.8],
    [41, 27.1],
    [43, 24.5],
    [45, 21.8],
    [46, 19.2],
    [47, 19.79],
  ];

  // S&P 500 waypoints (ends at -0.76%)
  const spWaypoints: [number, number][] = [
    [0, 0],
    [5, 0.8],
    [10, 1.5],
    [15, 2.1],
    [20, 1.8],
    [25, 1.2],
    [30, 0.5],
    [33, -0.3],
    [35, -0.9],
    [37, -1.5],
    [39, -1.2],
    [41, -0.8],
    [43, -0.5],
    [45, -0.6],
    [46, -0.7],
    [47, -0.76],
  ];

  function interpolate(wps: [number, number][], day: number): number {
    if (day <= wps[0][0]) return wps[0][1];
    if (day >= wps[wps.length - 1][0]) return wps[wps.length - 1][1];
    for (let i = 1; i < wps.length; i++) {
      if (day <= wps[i][0]) {
        const t = (day - wps[i - 1][0]) / (wps[i][0] - wps[i - 1][0]);
        return wps[i - 1][1] + t * (wps[i][1] - wps[i - 1][1]);
      }
    }
    return wps[wps.length - 1][1];
  }

  function seededRandom(seed: number) {
    const x = Math.sin(seed * 9301 + 49297) * 49297;
    return x - Math.floor(x);
  }

  const startDate = new Date("2026-01-01");
  const data: {
    date: string;
    strategyReturn: number;
    benchmarkReturn: number;
  }[] = [];

  let tradingDay = 0;

  for (let cal = 0; cal < 68; cal++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + cal);

    const dow = date.getDay();
    if (dow === 0 || dow === 6) continue;

    const noise = (seededRandom(tradingDay * 7 + 3) - 0.5) * 0.4;
    const spNoise = (seededRandom(tradingDay * 13 + 7) - 0.5) * 0.15;

    data.push({
      date: date.toISOString().split("T")[0],
      strategyReturn: parseFloat(
        (interpolate(waypoints, tradingDay) + noise).toFixed(2)
      ),
      benchmarkReturn: parseFloat(
        (interpolate(spWaypoints, tradingDay) + spNoise).toFixed(2)
      ),
    });

    tradingDay++;
  }

  return data;
}

export const equityCurve = generateEquityCurve();

export const summaryMetrics = {
  annualizedReturn: "+19.79%",
  sharpeRatio: "2.84",
  maxDrawdown: "-16.2%",
  annualizedVol: "28.4%",
};
