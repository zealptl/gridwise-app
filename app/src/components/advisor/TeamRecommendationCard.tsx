interface Driver {
  name: string
  team: string
  price: number
  reason: string
}

interface Constructor {
  name: string
  price: number
  reason: string
}

interface TeamRecommendation {
  drivers: Driver[]
  constructors: Constructor[]
  drs_boost: string
  transfers: { in: string[]; out: string[] }
  chip_advice: string | null
  total_cost: number
  confidence: string
}

interface Props {
  recommendation: TeamRecommendation
  status?: string
}

export function TeamRecommendationCard({ recommendation, status }: Props) {
  if (status === 'inProgress') {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4 animate-pulse">
        <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-3 w-full bg-gray-100 rounded" />
          ))}
        </div>
      </div>
    )
  }

  const { drivers = [], constructors = [], drs_boost, transfers, chip_advice, total_cost, confidence } = recommendation

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden w-full max-w-lg">
      <div className="bg-gray-900 px-4 py-3 flex items-center justify-between">
        <span className="text-white font-semibold text-sm">Team Recommendation</span>
        <span className="text-xs text-gray-400 capitalize">{confidence} confidence</span>
      </div>

      <div className="p-4 space-y-4">
        {/* Drivers */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Drivers</h3>
          <ul className="space-y-1">
            {drivers.map((d, i) => (
              <li key={i} className="flex items-start justify-between gap-2 text-sm">
                <div>
                  <span className="font-medium text-gray-900">{d.name}</span>
                  {d.name === drs_boost && (
                    <span className="ml-1.5 inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-700">DRS</span>
                  )}
                  <span className="ml-1.5 text-gray-500 text-xs">{d.team}</span>
                </div>
                <span className="text-gray-700 font-medium shrink-0">£{d.price.toFixed(1)}m</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Constructors */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Constructors</h3>
          <ul className="space-y-1">
            {constructors.map((c, i) => (
              <li key={i} className="flex items-center justify-between text-sm">
                <span className="font-medium text-gray-900">{c.name}</span>
                <span className="text-gray-700 font-medium">£{c.price.toFixed(1)}m</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Transfers */}
        {(transfers?.in?.length > 0 || transfers?.out?.length > 0) && (
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Transfers</h3>
            <div className="flex gap-4 text-sm">
              {transfers.in?.length > 0 && (
                <div>
                  <span className="text-green-600 font-medium">IN: </span>
                  {transfers.in.join(', ')}
                </div>
              )}
              {transfers.out?.length > 0 && (
                <div>
                  <span className="text-red-600 font-medium">OUT: </span>
                  {transfers.out.join(', ')}
                </div>
              )}
            </div>
          </section>
        )}

        {/* Chip advice */}
        {chip_advice && (
          <section className="rounded-md bg-blue-50 px-3 py-2">
            <span className="text-xs font-semibold text-blue-700">Chip: </span>
            <span className="text-xs text-blue-900">{chip_advice}</span>
          </section>
        )}

        {/* Total cost */}
        <div className="border-t pt-3 flex items-center justify-between text-sm">
          <span className="text-gray-500">Total cost</span>
          <span className="font-semibold text-gray-900">£{total_cost?.toFixed(1)}m</span>
        </div>
      </div>
    </div>
  )
}
