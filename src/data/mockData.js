const sites = [
  "Alle lokaliteter",
  "Hitra Nord",
  "Frøya Vest",
  "Senja Øst",
  "Alta Sør",
];

const regionsBySite = {
  "Hitra Nord": "Midt",
  "Frøya Vest": "Midt",
  "Senja Øst": "Nord",
  "Alta Sør": "Nord",
};

const siteList = sites.filter((site) => site !== "Alle lokaliteter");
const startDate = new Date("2026-02-25T00:00:00");

const dateToString = (inputDate) => {
  const year = inputDate.getFullYear();
  const month = String(inputDate.getMonth() + 1).padStart(2, "0");
  const day = String(inputDate.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const mockProductionData = Array.from({ length: 28 }).flatMap((_, dayOffset) => {
  const date = new Date(startDate);
  date.setDate(startDate.getDate() + dayOffset);

  return siteList.map((siteName, siteIndex) => {
    const harvestedKg = Math.round(
      59000 +
        siteIndex * 5200 +
        dayOffset * 430 +
        ((dayOffset + siteIndex) % 5) * 820,
    );
    const feedKg = Math.round(harvestedKg * (1.16 + siteIndex * 0.03));
    const dieselLiters = Math.round(980 + siteIndex * 120 + dayOffset * 6);
    const electricityKwh = Math.round(24000 + siteIndex * 1400 + dayOffset * 95);
    const co2eKg = Math.round(feedKg * 1.6 + dieselLiters * 2.68 + electricityKwh * 0.018);
    const mortalityRatePct = Number(
      (
        1.05 +
        siteIndex * 0.18 +
        ((dayOffset % 6) - 2.5) * 0.06
      ).toFixed(2),
    );

    return {
      date: dateToString(date),
      site: siteName,
      region: regionsBySite[siteName],
      harvestedKg,
      feedKg,
      dieselLiters,
      electricityKwh,
      co2eKg,
      mortalityRatePct,
    };
  });
});

export const locationOptions = sites;
