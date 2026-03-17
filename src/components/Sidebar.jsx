export default function Sidebar() {
  return (
    <aside className="w-72 shrink-0 border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#005B99]">
          Cermaq
        </p>
        <h1 className="mt-1 text-xl font-semibold text-slate-900">
          Sustainability Hub
        </h1>
      </div>

      <nav className="px-4 py-6">
        <p className="px-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          Rapportering
        </p>
        <ul className="mt-3 space-y-1">
          <li className="rounded-md bg-[#005B99]/10 px-3 py-2 text-sm font-medium text-[#005B99]">
            Bærekraftsoversikt
          </li>
          <li className="rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100">
            Miljøindikatorer
          </li>
          <li className="rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100">
            Produksjon og slakt
          </li>
          <li className="rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100">
            HMS og sosial påvirkning
          </li>
        </ul>
      </nav>

      <div className="mx-4 mt-6 rounded-lg border border-[#F58B1F]/40 bg-[#F58B1F]/10 p-4">
        <p className="text-xs uppercase tracking-[0.14em] text-[#BA6308]">
          Data status
        </p>
        <p className="mt-1 text-sm text-[#9A5005]">
          Mock-data fra Fishtalk Power BI-modell for UI-validering.
        </p>
      </div>
    </aside>
  );
}
