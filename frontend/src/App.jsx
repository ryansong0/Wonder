import React, { useEffect, useState } from 'react';
import { DollarSign, Percent, Search, FileText, Sparkles, Sliders, Landmark, AlertTriangle } from 'lucide-react';

const US_STATES = [
  { code: "AK", name: "Alaska" }, { code: "AL", name: "Alabama" }, { code: "AR", name: "Arkansas" },
  { code: "AZ", name: "Arizona" }, { code: "CA", name: "California" }, { code: "CO", name: "Colorado" },
  { code: "CT", name: "Connecticut" }, { code: "DE", name: "Delaware" }, { code: "FL", name: "Florida" },
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

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [backendError, setBackendError] = useState(null);
  const [evaluatedCollege, setEvaluatedCollege] = useState("");
  const [methodology, setMethodology] = useState("");

  const [universitySearch, setUniversitySearch] = useState("");
  const [householdIncome, setHouseholdIncome] = useState("");
  const [totalAssets, setTotalAssets] = useState("");
  const [familySize, setFamilySize] = useState("4");
  const [studentState, setStudentState] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/colleges`)
      .then((res) => res.json())
      .then(setColleges)
      .catch(() => setBackendError("Could not load the college list. Confirm Uvicorn is running on port 8000."));
  }, []);

  const triggerSimulation = async () => {
    const matchedCollege = colleges.find(c => c.college_name.toLowerCase() === universitySearch.toLowerCase());
    if (!matchedCollege || !householdIncome || !totalAssets || !familySize || !studentState) {
      setBackendError("Please select a university from the list and populate all profile inputs before computing.");
      return;
    }
    setLoading(true);
    setBackendError(null);
    try {
      const response = await fetch(`${API_BASE}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          college_name: matchedCollege.college_name,
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
      setMetrics(data.summary);
      setExplanation(data.explanation);
      setEvaluatedCollege(data.college_evaluated);
      setMethodology(data.methodology);
    } catch (err) {
      setBackendError("Stochastic backend microservice unreachable. Confirm Uvicorn is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans antialiased">
      <header className="max-w-6xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-900 pb-6 gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            WONDER <span className="text-indigo-400 font-light">MONTE CARLO AID ENGINE</span>
          </h1>
          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
            Your Financial Aid Tracker
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
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">US University Target</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3.5 text-slate-500" size={16} />
                  <input
                    type="text"
                    value={universitySearch}
                    onChange={(e) => setUniversitySearch(e.target.value)}
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
                  onChange={(e) => setStudentState(e.target.value.toUpperCase())}
                  placeholder="AK"
                  list="states-list"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all uppercase font-medium"
                  maxLength={2}
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
            <button onClick={triggerSimulation} disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-950 text-white font-bold py-3 px-4 rounded-xl transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-widest">
              {loading ? <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Sparkles size={14} />}
              {loading ? "Running Monte Carlo Simulation..." : "Run Aid Uncertainty Simulation"}
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {metrics ? (
            <>
              <div className="flex flex-wrap gap-3">
                <div className="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-xs font-semibold text-indigo-400 flex items-center gap-2">
                  Target: <span className="text-white font-bold">{evaluatedCollege}</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-xs font-semibold text-emerald-400 flex items-center gap-2">
                  <Landmark size={14} />
                  Aid Methodology: <span className="text-white font-bold">{methodology}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3 mb-2 text-slate-400">
                    <div className="p-2 bg-pink-500/10 text-pink-400 rounded-lg"><Percent size={16} /></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Probability of Shortfall</span>
                  </div>
                  <p className="text-2xl font-black text-white font-mono">
                    {(metrics.probability_of_shortfall * 100).toFixed(0)}%
                  </p>
                  <span className="text-[11px] text-slate-500 block mt-1">Share of simulated scenarios where savings don't cover the net cost.</span>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3 mb-2 text-slate-400">
                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg"><DollarSign size={16} /></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Likely Shortfall Range</span>
                  </div>
                  <p className="text-2xl font-black text-white font-mono">
                    ${metrics.shortfall_range_low.toLocaleString(undefined, {maximumFractionDigits: 0})} - ${metrics.shortfall_range_high.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </p>
                  <span className="text-[11px] text-slate-500 block mt-1">5th to 95th percentile across all simulated trials.</span>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3 mb-2 text-slate-400">
                    <div className="p-2 bg-rose-500/10 text-rose-400 rounded-lg"><AlertTriangle size={16} /></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Worst-Case Shortfall</span>
                  </div>
                  <p className="text-2xl font-black text-white font-mono">
                    ${metrics.worst_case_shortfall.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </p>
                  <span className="text-[11px] text-slate-500 block mt-1">Maximum shortfall observed across all simulated trials.</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md relative overflow-hidden">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <FileText size={16} className="text-indigo-400" />
                  Simulation Summary
                </h3>
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 leading-relaxed font-medium">
                  {explanation}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full min-h-[350px] border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 text-slate-500 bg-slate-900/10">
              <FileText size={32} className="mb-3 text-slate-600" />
              <p className="text-sm font-bold text-slate-400">System Standing By</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Enter your financial profile and pick a university to run a Monte Carlo simulation of your aid uncertainty.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
