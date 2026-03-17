import { useMemo, useState } from "react";
import { AreaChart, BarChart, Card, Text, Title } from "@tremor/react";
import KpiCard from "./components/KpiCard";
import Sidebar from "./components/Sidebar";
import TopFilters from "./components/TopFilters";
import { locationOptions, mockProductionData } from "./data/mockData";

const toDateString = (dateInput) => {
  const date = new Date(dateInput);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const shiftDateString = (dateString, dayOffset) => {
  const date = new Date(`${dateString}T00:00:00`);
  date.setDate(date.getDate() + dayOffset);
  return toDateString(date);
};

const daySpan = (startDate, endDate) => {
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  return Math.max(1, Math.round((end - start) / 86400000) + 1);
};

const aggregateByDate = (records) => {
  const grouped = new Map();
  records.forEach((entry) => {
    const existing = grouped.get(entry.date) ?? {
      date: entry.date,
      co2eKg: 0,
      harvestedKg: 0,
      mortalityRateTotal: 0,
      count: 0,
    };

    existing.co2eKg += entry.co2eKg;
    existing.harvestedKg += entry.harvestedKg;
    existing.mortalityRateTotal += entry.mortalityRatePct;
    existing.count += 1;
    grouped.set(entry.date, existing);
  });

  return [...grouped.values()]
    .sort((left, right) => left.date.localeCompare(right.date))
    .map((entry) => ({
      date: entry.date,
      co2eKg: Math.round(entry.co2eKg),
      harvestedKg: Math.round(entry.harvestedKg),
      mortalityRatePct: Number((entry.mortalityRateTotal / entry.count).toFixed(2)),
    }));
};

const summarize = (records) => {
  if (records.length === 0) {
    return {
      co2eKg: 0,
      harvestedKg: 0,
      avgMortalityRatePct: 0,
      avgFeedConversionRatio: 0,
    };
  }

  const totals = records.reduce(
    (accumulator, entry) => {
      accumulator.co2eKg += entry.co2eKg;
      accumulator.harvestedKg += entry.harvestedKg;
      accumulator.feedKg += entry.feedKg;
      accumulator.mortalityRate += entry.mortalityRatePct;
      return accumulator;
    },
    { co2eKg: 0, harvestedKg: 0, feedKg: 0, mortalityRate: 0 },
  );

  return {
    co2eKg: Math.round(totals.co2eKg),
    harvestedKg: Math.round(totals.harvestedKg),
    avgMortalityRatePct: Number((totals.mortalityRate / records.length).toFixed(2)),
    avgFeedConversionRatio: Number((totals.feedKg / totals.harvestedKg).toFixed(2)),
  };
};

const calculateDeltaPercent = (currentValue, previousValue) => {
  if (!previousValue) {
    return 0;
  }
  return Number((((currentValue - previousValue) / previousValue) * 100).toFixed(1));
};

const deltaTypeFromPercent = (percentChange, isIncreasePositive) => {
  const absolute = Math.abs(percentChange);
  if (absolute < 0.5) {
    return "unchanged";
  }

  if (percentChange > 0) {
    if (isIncreasePositive) {
      return absolute > 5 ? "increase" : "moderateIncrease";
    }
    return absolute > 5 ? "decrease" : "moderateDecrease";
  }

  if (isIncreasePositive) {
    return absolute > 5 ? "decrease" : "moderateDecrease";
  }
  return absolute > 5 ? "increase" : "moderateIncrease";
};

const formatNumber = (value) => new Intl.NumberFormat("no-NO").format(value);
const formatPercent = (value) =>
  `${value > 0 ? "+" : ""}${new Intl.NumberFormat("no-NO", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)}%`;

function App() {
  const allDates = useMemo(
    () => [...new Set(mockProductionData.map((entry) => entry.date))].sort(),
    [],
  );

  const minDate = allDates[0];
  const maxDate = allDates[allDates.length - 1];
  const defaultStartDate = shiftDateString(maxDate, -13);

  const [selectedSite, setSelectedSite] = useState("Alle lokaliteter");
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [endDate, setEndDate] = useState(maxDate);

  const normalizedStartDate = startDate <= endDate ? startDate : endDate;
  const normalizedEndDate = startDate <= endDate ? endDate : startDate;

  const filteredRecords = useMemo(
    () =>
      mockProductionData.filter((entry) => {
        const insideDateRange =
          entry.date >= normalizedStartDate && entry.date <= normalizedEndDate;
        const insideSite =
          selectedSite === "Alle lokaliteter" || entry.site === selectedSite;
        return insideDateRange && insideSite;
      }),
    [normalizedEndDate, normalizedStartDate, selectedSite],
  );

  const previousPeriodRecords = useMemo(() => {
    const periodLength = daySpan(normalizedStartDate, normalizedEndDate);
    const previousEndDate = shiftDateString(normalizedStartDate, -1);
    const previousStartDate = shiftDateString(previousEndDate, -(periodLength - 1));
    return mockProductionData.filter((entry) => {
      const insideDateRange =
        entry.date >= previousStartDate && entry.date <= previousEndDate;
      const insideSite =
        selectedSite === "Alle lokaliteter" || entry.site === selectedSite;
      return insideDateRange && insideSite;
    });
  }, [normalizedEndDate, normalizedStartDate, selectedSite]);

  const currentSummary = useMemo(() => summarize(filteredRecords), [filteredRecords]);
  const previousSummary = useMemo(
    () => summarize(previousPeriodRecords),
    [previousPeriodRecords],
  );
  const chartRows = useMemo(() => aggregateByDate(filteredRecords), [filteredRecords]);

  const co2eDelta = calculateDeltaPercent(
    currentSummary.co2eKg,
    previousSummary.co2eKg,
  );
  const mortalityDelta = calculateDeltaPercent(
    currentSummary.avgMortalityRatePct,
    previousSummary.avgMortalityRatePct,
  );
  const harvestedDelta = calculateDeltaPercent(
    currentSummary.harvestedKg,
    previousSummary.harvestedKg,
  );

  const emissionTrend = chartRows.map((entry) => ({
    Dato: entry.date,
    "CO2e (kg)": entry.co2eKg,
  }));

  const harvestTrend = chartRows.map((entry) => ({
    Dato: entry.date,
    "Slaktet volum (kg)": entry.harvestedKg,
  }));

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="flex min-h-screen">
        <Sidebar />

        <main className="flex-1">
          <TopFilters
            locationOptions={locationOptions}
            selectedSite={selectedSite}
            startDate={normalizedStartDate}
            endDate={normalizedEndDate}
            onSelectedSiteChange={setSelectedSite}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
          />

          <div className="space-y-6 p-7">
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                title="Totale utslipp"
                value={formatNumber(currentSummary.co2eKg)}
                unit="kg CO2e"
                deltaText={formatPercent(co2eDelta)}
                deltaType={deltaTypeFromPercent(co2eDelta, false)}
                isIncreasePositive={false}
              />
              <KpiCard
                title="Snitt dødelighet"
                value={currentSummary.avgMortalityRatePct}
                unit="%"
                deltaText={formatPercent(mortalityDelta)}
                deltaType={deltaTypeFromPercent(mortalityDelta, false)}
                isIncreasePositive={false}
              />
              <KpiCard
                title="Slaktet volum"
                value={formatNumber(currentSummary.harvestedKg)}
                unit="kg"
                deltaText={formatPercent(harvestedDelta)}
                deltaType={deltaTypeFromPercent(harvestedDelta, true)}
                isIncreasePositive
              />
              <Card className="border border-slate-200 shadow-sm">
                <Text>Snitt FCR</Text>
                <p className="mt-3 text-4xl font-semibold text-[#005B99]">
                  {currentSummary.avgFeedConversionRatio}
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  Sammenlikning mot forrige periode vises i KPI-kortene.
                </p>
              </Card>
            </section>

            <section className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
              <Card className="border border-slate-200 shadow-sm">
                <Title className="text-slate-900">CO2e trend per dag</Title>
                <Text className="text-slate-500">
                  AreaChart fra Tremor med mock-data fra Fishtalk/Power BI-modell.
                </Text>
                <AreaChart
                  className="mt-5 h-72"
                  data={emissionTrend}
                  index="Dato"
                  categories={["CO2e (kg)"]}
                  colors={["blue"]}
                  curveType="monotone"
                  valueFormatter={(value) => `${formatNumber(Math.round(value))} kg`}
                  yAxisWidth={70}
                />
              </Card>

              <Card className="border border-slate-200 shadow-sm">
                <Title className="text-slate-900">Slaktet volum per dag</Title>
                <Text className="text-slate-500">
                  BarChart fra Tremor, klar til senere API-kobling mot Fishtalk.
                </Text>
                <BarChart
                  className="mt-5 h-72"
                  data={harvestTrend}
                  index="Dato"
                  categories={["Slaktet volum (kg)"]}
                  colors={["orange"]}
                  valueFormatter={(value) => `${formatNumber(Math.round(value))} kg`}
                  yAxisWidth={70}
                />
              </Card>
            </section>

            <Card className="border border-[#F58B1F]/40 bg-[#F58B1F]/5 shadow-sm">
              <Title className="text-slate-900">Datagrunnlag</Title>
              <Text className="text-slate-600">
                Mockdatasettet inneholder {mockProductionData.length} observasjoner fordelt
                på 4 lokaliteter i perioden {minDate} til {maxDate}. Dette simulerer feltene
                fra Power BI-modellen slik at vi kan kvalitetssikre frontend før API-integrasjon.
              </Text>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
