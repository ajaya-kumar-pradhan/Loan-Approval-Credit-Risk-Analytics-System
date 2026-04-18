import { useState } from 'react'

function App() {
  // We keep track of all form inputs in one state object for simplicity
  const [formData, setFormData] = useState({
    loan_amount: 10000,
    annual_inc: 50000,
    interest_rate: 12.5,
    dti: 15.0,
    installment: 320.0,
    term: "36 months",
    emp_length_int: 5.0,
    grade: "B"
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Helper to update state as user types
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // We use a relative path so it works both locally and in production
      const response = await fetch('/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          // Convert strings to floats where needed
          loan_amount: parseFloat(formData.loan_amount),
          annual_inc: parseFloat(formData.annual_inc),
          interest_rate: parseFloat(formData.interest_rate),
          dti: parseFloat(formData.dti),
          installment: parseFloat(formData.installment),
          emp_length_int: parseFloat(formData.emp_length_int),
        }),
      });

      if (!response.ok) {
        throw new Error('Server responded with an error. Is the backend running?');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="glass-card">
      <header>
        <h1>Credit Risk IQ</h1>
        <p className="subtitle">Real-time Loan Default Prediction System</p>
      </header>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          {/* Row 1 */}
          <div className="input-group">
            <label>Loan Amount ($)</label>
            <input 
              name="loan_amount" 
              type="number" 
              value={formData.loan_amount} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="input-group">
            <label>Annual Income ($)</label>
            <input 
              name="annual_inc" 
              type="number" 
              value={formData.annual_inc} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="input-group">
            <label>Interest Rate (%)</label>
            <input 
              name="interest_rate" 
              type="number" 
              step="0.01" 
              value={formData.interest_rate} 
              onChange={handleChange} 
              required 
            />
          </div>

          {/* Row 2 */}
          <div className="input-group">
            <label>Debt-to-Income (%)</label>
            <input 
              name="dti" 
              type="number" 
              step="0.1" 
              value={formData.dti} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="input-group">
            <label>Monthly Installment</label>
            <input 
              name="installment" 
              type="number" 
              value={formData.installment} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="input-group">
            <label>Loan Term</label>
            <select name="term" value={formData.term} onChange={handleChange}>
              <option value="36 months">36 Months</option>
              <option value="60 months">60 Months</option>
            </select>
          </div>

          {/* Row 3 */}
          <div className="input-group">
            <label>Employment (Years)</label>
            <input 
              name="emp_length_int" 
              type="number" 
              value={formData.emp_length_int} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className="input-group">
            <label>Credit Grade</label>
            <select name="grade" value={formData.grade} onChange={handleChange}>
              {['A','B','C','D','E','F','G'].map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing Risk...' : 'Run Risk Assessment'}
        </button>
      </form>

      {error && (
        <div className="result-area" style={{color: 'var(--danger)'}}>
          <p>⚠️ {error}</p>
        </div>
      )}

      {result && (
        <section className="result-area">
          <div style={{display: 'flex', alignItems: 'center', gap: '2rem'}}>
            <div className="prob-circle">
              <span className="prob-value">{result.default_probability}%</span>
              <span className="prob-label">Default Prob</span>
            </div>
            
            <div>
              <div className={`risk-badge risk-${result.risk_level.replace(' ', '-')}`}>
                Risk Level: {result.risk_level}
              </div>
              <p style={{fontSize: '1.2rem'}}>
                The application was evaluated as <strong>{result.is_risky ? 'High Risk' : 'Low Risk'}</strong>.
              </p>
              <p style={{color: 'var(--text-muted)', marginTop: '0.5rem'}}>
                Prediction based on Random Forest classifier artifacts.
              </p>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}

export default App
