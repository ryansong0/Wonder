import React, { useState } from 'react';
import { DollarSign, Percent, Search, Bot, FileText, Sparkles, Sliders, Landmark } from 'lucide-react';

// Top 40 US Colleges Data Array for Quick Prefills (Estimated 2026 Cost of Attendance)
const TOP_COLLEGES = [
  { name: "Princeton University", coa: 90730 },
  { name: "Harvard University", coa: 89315 },
  { name: "Duke University", coa: 92042 },
  { name: "Massachusetts Institute of Technology", coa: 90500 },
  { name: "Stanford University", coa: 91200 },
  { name: "Yale University", coa: 91800 },
  { name: "University of Pennsylvania", coa: 92200 },
  { name: "California Institute of Technology", coa: 89500 },
  { name: "Brown University", coa: 91500 },
  { name: "Johns Hopkins University", coa: 88900 },
  { name: "Northwestern University", coa: 91200 },
  { name: "Columbia University", coa: 93100 },
  { name: "Cornell University", coa: 90200 },
  { name: "University of Chicago", coa: 91800 },
  { name: "Dartmouth College", coa: 91600 },
  { name: "Vanderbilt University", coa: 89900 },
  { name: "Rice University", coa: 85500 },
  { name: "Washington University in St. Louis", coa: 90100 },
  { name: "University of Notre Dame", coa: 89200 },
  { name: "Emory University", coa: 88400 },
  { name: "Georgetown University", coa: 89700 },
  { name: "Carnegie Mellon University", coa: 90400 },
  { name: "New York University", coa: 93200 },
  { name: "University of Southern California", coa: 92500 },
  { name: "Tufts University", coa: 92100 },
  { name: "Boston College", coa: 91400 },
  { name: "Wake Forest University", coa: 88200 },
  { name: "University of Michigan", coa: 76500 },
  { name: "University of Virginia", coa: 74200 },
  { name: "University of North Carolina at Chapel Hill", coa: 61800 },
  { name: "University of California, Berkeley", coa: 78500 },
  { name: "University of California, Los Angeles", coa: 77200 },
  { name: "University of California, San Diego", coa: 75900 },
  { name: "University of California, Irvine", coa: 74800 },
  { name: "University of California, Santa Barbara", coa: 76100 },
  { name: "University of Florida", coa: 48500 },
  { name: "University of Texas at Austin", coa: 59200 },
  { name: "Georgia Institute of Technology", coa: 54500 },
  { name: "University of Illinois Urbana-Champaign", coa: 61200 },
  { name: "University of Wisconsin-Madison", coa: 58400 }
];

export default function App() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [aiResponse, setAiResponse] = useState("");
  const [backendError, setBackendError] = useState(null);
  const [evaluatedCollege, setEvaluatedCollege] = useState("");
  const [endowmentScale, setEndowmentScale] = useState("");
  
  // State management for user input parameters
  const [universitySearch, setUniversitySearch] = useState("Duke University");
  const [manualCoa, setManualCoa] = useState(92042);
  const [householdIncome, setHouseholdIncome] = useState(100000);
  const [studentState, setStudentState] = useState("AK");

  // Automatically adjust baseline COA when a target university is selected
  const handleUniversityChange = (val) => {
    setUniversitySearch(val);
    const matched = TOP_COLLEGES.find(c => c.name.toLowerCase() === val.toLowerCase());
    if (matched) {
      setManualCoa(matched.coa);
    }
  };

  const triggerSimulation = async () => {
    setLoading(true);
    setBackendError(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          college: { name: universitySearch, tuition: Number(manualCoa) }, // Mapped to expected schema
          student: { household_income: Number(householdIncome), assets: 0, size: 4, state: studentState },
          runs: 5000
        })
      });
      
      if (!response.ok) throw new Error("Server response malfunctioned.");
      
      const data = await response.json();
      setMetrics(data.summary);
      setAiResponse(data.ai_analysis);
      setEvaluatedCollege(data.college_evaluated);
      setEndowmentScale(data.endowment);
    } catch (err) {
      setBackendError("Stochastic backend microservice unreachable. Confirm Uvicorn is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans antialiased">
      {/* App Header */}
      <header className="max-w-6xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-900 pb-6 gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            WONDER <span className="text-indigo-400 font-light">AI ANALYTICS ENGINE</span>
          </h1>
          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
            Your Financial Aid Tracker
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Control Panel */}
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
                    onChange={(e) => handleUniversityChange(e.target.value)} 
                    placeholder="e.g., Duke University, Stanford..." 
                    list="colleges-list"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 pl-10 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-medium" 
                  />
                  <datalist id="colleges-list">
                    {TOP_COLLEGES.map((college, idx) => (
                      <option key={idx} value={college.name} />
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
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Home State</label>
                  <input type="text" value={studentState} onChange={(e) => setStudentState(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all uppercase" maxLength={2} />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">COA Fallback ($)</label>
                  <input type="number" value={manualCoa} onChange={(e) => setManualCoa(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-mono" />
                </div>
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
              {loading ? "Analyzing Institutional Data..." : "Compute Net Price Variance"}
            </button>
          </div>
        </div>

        {/* Right Outputs Visualization */}
        <div className="lg:col-span-2 space-y-6">
          {metrics ? (
            <>
              <div className="flex flex-wrap gap-3">
                <div className="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-xs font-semibold text-indigo-400 flex items-center gap-2">
                  Target: <span className="text-white font-bold">{evaluatedCollege}</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl text-xs font-semibold text-emerald-400 flex items-center gap-2">
                  <Landmark size={14} />
                  Est. Endowment Size: <span className="text-white font-bold">{endowmentScale}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3 mb-2 text-slate-400">
                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg"><DollarSign size={16} /></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Estimated Net Out-Of-Pocket Range</span>
                  </div>
                  <p className="text-2xl font-black text-white font-mono">
                    ${metrics.range_low.toLocaleString(undefined, {maximumFractionDigits: 0})} - ${metrics.range_high.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </p>
                  <span className="text-[11px] text-slate-500 block mt-1">Adjusted for custom institutional endowment posture and grant patterns.</span>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
                  <div className="flex items-center gap-3 mb-2 text-slate-400">
                    <div className="p-2 bg-pink-500/10 text-pink-400 rounded-lg"><Percent size={16} /></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Estimated Net Cost Volatility Risk</span>
                  </div>
                  <p className="text-2xl font-black text-white font-mono">
                    {(metrics.risk_of_shortfall * 100).toFixed(0)}%
                  </p>
                  <span className="text-[11px] text-slate-500 block mt-1">Relative debt/shortfall probability based on income brackets.</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md relative overflow-hidden">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Bot size={16} className="text-indigo-400" />
                  Local LLM Diagnostic Attribution
                </h3>
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 leading-relaxed font-medium">
                  {aiResponse}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full min-h-[350px] border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 text-slate-500 bg-slate-900/10">
              <FileText size={32} className="mb-3 text-slate-600" />
              <p className="text-sm font-bold text-slate-400">System Standing By</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Enter an institutional target and income boundaries to trigger the local Ollama deep analysis layer.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}