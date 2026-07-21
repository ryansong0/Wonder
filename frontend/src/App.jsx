import React, { useEffect, useState } from 'react';
import { DollarSign, Percent, Search, FileText, Sparkles, Sliders, Landmark, X, ChevronDown, BadgeCheck } from 'lucide-react';

const US_STATES = [
  { code: "AK", name: "Alaska" }, { code: "AL", name: "Alabama" }, { code: "AR", name: "Arkansas" },
  { code: "AZ", name: "Arizona" }, { code: "CA", name: "California" }, { code: "CO", name: "Colorado" },
  { code: "CT", name: "Connecticut" }, { code: "DE", name: "Delaware" }, { code: "DC", name: "District of Columbia" }, { code: "FL", name: "Florida" },
  { code: "GA", name: "Georgia" }, { code: "HI", name: "Hawaii" }, { code: "IA", name: "Iowa" },
  { code: "ID", name: "Idaho" }, { code: "IL", name: "Illinois" }, { code: "IN", name: "Indiana" },
  { code: "KS", name: "Kansas" }, { code: "KY", name: "Kentucky" }, { code: "LA", name: "Louisiana" },
  { code: "MA", name: "Massachusetts" }, { code: "MD", name: "Maryland" }, { code: "ME", name: "Maine" },
  { code: "MI", name: "Michigan" }, { code: "MN", name: "Minnesota" }, { code: "MO", name: "Missouri" },
  { code: "MS", name: "Mississippi" }, { code: "MT", name: "Montana" }, { code: "NC", name: "North Carolina" },
  { code: "ND", name: "North Dakota" }, { code: "NE", name: "Nebraska" }, { code: "NH", name: "New Hampshire" },
  { code: "NJ", name: "New Jersey" }, { code: "NM", name: "New Mexico" }, { code: "NV", name: "Nevada" },
  { code: "NY", name: "New York" }, { code: "OH", name: "Ohio" }, { code: "OK", name: "Oklahoma" },
  { code: "OR", name: "Oregon" }, { code: "PA", name: "Pennsylvania" }, { code: "RI", name: "Rhode Island" },
  { code: "SC", name: "South Carolina" }, { code: "SD", name: "South Dakota" }, { code: "TN", name: "Tennessee" },
  { code: "TX", name: "Texas" }, { code: "UT", name: "Utah" }, { code: "VA", name: "Virginia" },
  { code: "VT", "name": "Vermont" }, { code: "WA", name: "Washington" }, { code: "WI", name: "Wisconsin" },
  { code: "WV", name: "West Virginia" }, { code: "WY", name: "Wyoming" }
];

// Strip any trailing slash so a mistyped env var (with or without one) can't
// produce a double-slash URL like "https://api.example.com//api/colleges".
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const MAX_COMPARISON_SIZE = 6;

function formatDollars(value) {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function ShortfallRangeRow({ result, maxScale, expanded, onToggle }) {
  const { summary } = result;
  const lowPct = (summary.net_price_range_low / maxScale) * 100;
  const highPct = (summary.net_price_range_high / maxScale) * 100;
  const avgPct = (summary.average_net_price / maxScale) * 100;
  const isCssProfile = result.methodology.startsWith("CSS");
  // 0.5% is the point below which the risk badge would display as "0% risk"
  // (it's rounded to the nearest whole percent) - showing the badge and the
  // shortfall callout only above that avoids the confusing "0% risk, here's
  // your shortfall" combination for a probability too small to round up.
  const hasShortfallRisk = summary.probability_of_shortfall >= 0.005;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <button onClick={onToggle} className="w-full text-left p-4 flex flex-col gap-3 hover:bg-slate-800/40 transition-colors">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-bold text-white truncate">{result.college_evaluated}</p>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-bold uppercase tracking-wider ${isCssProfile ? 'text-amber-400' : 'text-emerald-400'}`}>
                {result.methodology}
              </span>
              {summary.calibrated_with_real_data && (
                <span className="flex items-center gap-1 text-[10px] font-bold text-sky-400" title="Centered on this school's own published net price from the College Scorecard">
                  <BadgeCheck size={11} />
                  REAL DATA
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {hasShortfallRisk && (
              <div className="flex items-center gap-1.5 bg-pink-500/10 text-pink-400 text-xs font-bold px-2.5 py-1 rounded-lg">
                <Percent size={12} />
                {(summary.probability_of_shortfall * 100).toFixed(0)}% risk
              </div>
            )}
            <ChevronDown size={16} className={`text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </div>

        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Estimated total cost after aid (4 years)</span>
          <div className="relative w-full h-2.5 bg-slate-800 rounded-full mt-1.5">
            <div
              className="absolute h-2.5 bg-indigo-500 rounded-full"
              style={{ left: `${lowPct}%`, width: `${Math.max(highPct - lowPct, 1)}%` }}
            />
            <div
              className="absolute w-0.5 h-2.5 bg-white/80 rounded-full"
              style={{ left: `${avgPct}%` }}
              title={`Average: ${formatDollars(summary.average_net_price)}`}
            />
          </div>
          <div className="flex justify-between mt-1 text-[11px] text-slate-500 font-mono">
            <span>{formatDollars(summary.net_price_range_low)}</span>
            <span>{formatDollars(summary.net_price_range_high)}</span>
          </div>
        </div>

        {hasShortfallRisk && (
          <div className="text-[11px] text-rose-400 font-semibold">
            Typical shortfall if savings don't fully cover it: {formatDollars(summary.shortfall_range_low)} to {formatDollars(summary.shortfall_range_high)}
          </div>
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 text-sm text-slate-300 leading-relaxed border-t border-slate-800 pt-3">
          {result.explanation}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [expandedName, setExpandedName] = useState(null);
  const [backendError, setBackendError] = useState(null);

  const [universitySearch, setUniversitySearch] = useState("");
  const [selectedNames, setSelectedNames] = useState([]);
  const [householdIncome, setHouseholdIncome] = useState("");
  const [totalAssets, setTotalAssets] = useState("");
  const [familySize, setFamilySize] = useState("4");
  const [studentState, setStudentState] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/colleges`)
      .then((res) => res.json())
      .then(setColleges)
      .catch(() => setBackendError(`Could not load the college list from ${API_BASE}. Confirm the backend is running and reachable.`));
  }, []);

  const addCollege = () => {
    const matched = colleges.find(c => c.college_name.toLowerCase() === universitySearch.trim().toLowerCase());
    if (!matched) {
      setBackendError("Pick a university from the list before adding it.");
      return;
    }
    if (selectedNames.includes(matched.college_name)) {
      setUniversitySearch("");
      return;
    }
    if (selectedNames.length >= MAX_COMPARISON_SIZE) {
      setBackendError(`You can compare up to ${MAX_COMPARISON_SIZE} universities at a time.`);
      return;
    }
    setSelectedNames([...selectedNames, matched.college_name]);
    setUniversitySearch("");
    setBackendError(null);
  };

  const removeCollege = (name) => {
    setSelectedNames(selectedNames.filter(n => n !== name));
  };

  const triggerComparison = async () => {
    if (selectedNames.length === 0 || !householdIncome || !totalAssets || !familySize || !studentState) {
      setBackendError("Add at least one university and populate all profile inputs before computing.");
      return;
    }
    setLoading(true);
    setBackendError(null);
    try {
      const response = await fetch(`${API_BASE}/api/simulate/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          college_names: selectedNames,
          student: {
            household_income: Number(householdIncome),
            total_assets: Number(totalAssets),
            family_size: Number(familySize),
            state_of_residence: studentState,
          },
          runs: 5000
        })
      });

      if (!response.ok) throw new Error("Server response malfunctioned.");

      const data = await response.json();
      const sorted = [...data.results].sort((a, b) => b.summary.average_net_price - a.summary.average_net_price);
      setResults(sorted);
      setExpandedName(sorted.length > 0 ? sorted[0].college_evaluated : null);
      if (data.not_found.length > 0) {
        setBackendError(`No aid data available for: ${data.not_found.join(", ")}.`);
      }
    } catch (err) {
      setBackendError(`Could not reach the backend at ${API_BASE}. Confirm it's running and reachable.`);
    } finally {
      setLoading(false);
    }
  };

  const maxScale = results.length > 0 ? Math.max(...results.map(r => r.summary.net_price_range_high)) : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans antialiased">
      <header className="max-w-6xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-900 pb-6 gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            WONDER <span className="text-indigo-400 font-light">MONTE CARLO AID ENGINE</span>
          </h1>
          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
            Compare Your Financial Aid Across Universities
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-fit space-y-6">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
              <Sliders size={14} className="text-indigo-400" />
              Financial Profile Inputs
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Add University to Compare</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3.5 text-slate-500" size={16} />
                  <input
                    type="text"
                    value={universitySearch}
                    onChange={(e) => setUniversitySearch(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addCollege(); } }}
                    placeholder="Search university..."
                    list="colleges-list"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 pl-10 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-medium"
                  />
                  <datalist id="colleges-list">
                    {colleges.map((college, idx) => (
                      <option key={idx} value={college.college_name} />
                    ))}
                  </datalist>
                </div>
                {selectedNames.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {selectedNames.map((name) => (
                      <span key={name} className="flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold pl-3 pr-2 py-1.5 rounded-lg">
                        {name}
                        <button onClick={() => removeCollege(name)} className="hover:text-white transition-colors">
                          <X size={12} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Household Gross Income ($)</label>
                <input type="number" value={householdIncome} onChange={(e) => setHouseholdIncome(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-mono" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Total Assets ($)</label>
                  <input type="number" value={totalAssets} onChange={(e) => setTotalAssets(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Family Size</label>
                  <input type="number" min="1" value={familySize} onChange={(e) => setFamilySize(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-mono" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Home State</label>
                <input
                  type="text"
                  value={studentState}
                  onChange={(e) => setStudentState(e.target.value)}
                  placeholder="NC or North Carolina"
                  list="states-list"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-medium"
                />
                <datalist id="states-list">
                  {US_STATES.map((st, idx) => (
                    <option key={idx} value={st.code}>{st.name}</option>
                  ))}
                </datalist>
              </div>
            </div>
          </div>

          <div>
            {backendError && (
              <div className="text-xs text-rose-400 bg-rose-950/20 border border-rose-900/50 p-3 rounded-xl mb-3 font-medium">
                {backendError}
              </div>
            )}
            <button onClick={triggerComparison} disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-950 text-white font-bold py-3 px-4 rounded-xl transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-widest">
              {loading ? <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Sparkles size={14} />}
              {loading ? "Running Monte Carlo Simulation..." : "Compare Selected Universities"}
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {results.length > 0 ? (
            <>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 px-1">
                <DollarSign size={14} className="text-indigo-400" />
                Estimated total cost per university (5th to 95th percentile), sorted highest cost first. Shortfall risk shown separately when savings wouldn't fully cover it. Click a row for details.
              </div>
              {results.map((result) => (
                <ShortfallRangeRow
                  key={result.college_evaluated}
                  result={result}
                  maxScale={maxScale}
                  expanded={expandedName === result.college_evaluated}
                  onToggle={() => setExpandedName(expandedName === result.college_evaluated ? null : result.college_evaluated)}
                />
              ))}
            </>
          ) : (
            <div className="h-full min-h-[350px] border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 text-slate-500 bg-slate-900/10">
              <Landmark size={32} className="mb-3 text-slate-600" />
              <p className="text-sm font-bold text-slate-400">System Standing By</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Enter your financial profile, add up to {MAX_COMPARISON_SIZE} universities, and run the comparison to see your aid uncertainty side by side.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
