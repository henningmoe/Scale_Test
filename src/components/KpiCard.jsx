import { BadgeDelta, Card, Metric, Text } from "@tremor/react";

export default function KpiCard({
  title,
  value,
  unit,
  deltaText,
  deltaType,
  isIncreasePositive,
}) {
  return (
    <Card className="border border-slate-200 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <Text>{title}</Text>
        <BadgeDelta
          deltaType={deltaType}
          isIncreasePositive={isIncreasePositive}
          size="xs"
        >
          {deltaText}
        </BadgeDelta>
      </div>
      <Metric className="mt-3 text-[#005B99]">
        {value}
        <span className="ml-1 text-lg font-medium text-slate-500">{unit}</span>
      </Metric>
    </Card>
  );
}
