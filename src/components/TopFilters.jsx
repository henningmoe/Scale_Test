export default function TopFilters({
  locationOptions,
  selectedSite,
  startDate,
  endDate,
  onSelectedSiteChange,
  onStartDateChange,
  onEndDateChange,
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 bg-white px-7 py-5">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">
          Bærekraftsdashboard
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Clean enterprise visning av Cermaq KPI-er
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="space-y-1 text-sm text-slate-600">
          <span>Lokalitet</span>
          <select
            className="min-w-48 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none ring-[#005B99] focus:ring-2"
            value={selectedSite}
            onChange={(event) => onSelectedSiteChange(event.target.value)}
          >
            {locationOptions.map((site) => (
              <option key={site} value={site}>
                {site}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1 text-sm text-slate-600">
          <span>Fra dato</span>
          <input
            type="date"
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none ring-[#005B99] focus:ring-2"
            value={startDate}
            onChange={(event) => onStartDateChange(event.target.value)}
          />
        </label>

        <label className="space-y-1 text-sm text-slate-600">
          <span>Til dato</span>
          <input
            type="date"
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none ring-[#005B99] focus:ring-2"
            value={endDate}
            onChange={(event) => onEndDateChange(event.target.value)}
          />
        </label>
      </div>
    </header>
  );
}
