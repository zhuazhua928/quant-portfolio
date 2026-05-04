import summaryJson from "./energy/summary.json";
import pricesJson from "./energy/prices.json";
import curveJson from "./energy/curve.json";
import storageJson from "./energy/storage.json";

export interface ContangoScore {
  m1: number | null;
  m2: number | null;
  spread: number | null;
  label: "contango" | "backwardation" | "flat" | "n/a";
}

export interface WidowMaker {
  year: number;
  spread: number;
}

export interface WinterStrip {
  contracts: string[];
  average: number;
}

export interface SummerWinter {
  summer_avg: number;
  winter_avg: number;
  diff: number;
}

export interface FrontMonth {
  ticker: string;
  close: number;
  asof: string;
  change_d: number | null;
  change_d_pct: number | null;
  change_w_pct: number | null;
  vol_30d_annualized: number | null;
}

export interface SpotSnapshot {
  value: number;
  asof: string;
}

export interface StorageWeeklyChange {
  delta: number;
  label: "build" | "draw";
}

export interface StorageYoY {
  latest: number;
  year_ago: number;
  delta: number;
  pct: number | null;
}

export interface EnergySummary {
  asof: string;
  front_month: FrontMonth | null;
  spot: SpotSnapshot | null;
  curve: {
    asof: string;
    contango: ContangoScore;
    widow_maker: WidowMaker | null;
    winter_strip: WinterStrip | null;
    summer_winter: SummerWinter | null;
  };
  storage: {
    available: boolean;
    asof: string | null;
    latest: number | null;
    weekly_change: StorageWeeklyChange | null;
    yoy: StorageYoY | null;
    zscore: number | null;
  };
}

export interface EnergyPriceRow {
  date: string;
  close: number;
  log_ret: number | null;
  vol_10d: number | null;
  vol_30d: number | null;
}

export interface ForwardContract {
  symbol: string;
  year: number;
  month: number;
  expiry_label: string;
  close: number;
}

export interface EnergyCurve {
  asof: string;
  contracts: ForwardContract[];
  contango: ContangoScore;
  widow_maker: WidowMaker | null;
  winter_strip: WinterStrip | null;
  summer_winter: SummerWinter | null;
}

export interface StorageWeekly {
  date: string;
  value: number;
  year: number;
  week_of_year: number;
}

export interface StorageEnvelopeRow {
  week_of_year: number;
  min: number;
  p25: number;
  mean: number;
  p75: number;
  max: number;
}

export interface EnergyStorage {
  available: boolean;
  asof: string | null;
  weekly: StorageWeekly[];
  envelope: StorageEnvelopeRow[];
  latest: number | null;
  weekly_change: StorageWeeklyChange | null;
  yoy: StorageYoY | null;
  zscore: number | null;
}

export const energySummary = summaryJson as unknown as EnergySummary;
export const energyPrices = pricesJson as unknown as EnergyPriceRow[];
export const energyCurve = curveJson as unknown as EnergyCurve;
export const energyStorage = storageJson as unknown as EnergyStorage;
