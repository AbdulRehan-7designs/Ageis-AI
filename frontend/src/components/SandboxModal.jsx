import React, { useState } from 'react';
import { Terminal, Play, ShieldAlert, CheckCircle2, X, AlertTriangle } from 'lucide-react';
import { executeSandboxCode } from '../services/api';

export default function SandboxModal({ isOpen, onClose }) {
  const [code, setCode] = useState(`# Air-Gapped Sovereign Execution Sandbox
# Write diagnostic python code or industrial calculations

vibration_data = [4.2, 4.5, 4.8, 5.1, 5.4, 6.2, 7.8]
critical_threshold = 7.1

exceeded = [v for v in vibration_data if v > critical_threshold]
print(f"Total Readings: {len(vibration_data)}")
print(f"Exceeded Threshold (> {critical_threshold} mm/s): {exceeded}")
if exceeded:
    print("WARNING: Mandatory Pump Inspection Required as per SOP-017.")
`);
  const [result, setResult] = useState(null);
  const [executing, setExecuting] = useState(false);

  const handleRun = async () => {
    setExecuting(true);
    setResult(null);
    try {
      const res = await executeSandboxCode(code);
      setResult(res);
    } catch (err) {
      console.error(err);
      setResult({
        status: 'ERROR',
        stdout: '',
        stderr: err.response?.data?.detail || err.message,
        execution_time_sec: 0,
        violations: []
      });
    } finally {
      setExecuting(false);
    }
  };

  const loadPreset = (presetType) => {
    if (presetType === 'vibration') {
      setCode(`vibration_data = [4.2, 4.5, 4.8, 5.1, 5.4, 6.2, 7.8]
critical_threshold = 7.1
exceeded = [v for v in vibration_data if v > critical_threshold]
print(f"Total Readings: {len(vibration_data)}")
print(f"Exceeded (> {critical_threshold} mm/s): {exceeded}")
`);
    } else if (presetType === 'pressure') {
      setCode(`inlet_pressure = 4.2 # bar
outlet_pressure = 12.8 # bar
head_pressure = outlet_pressure - inlet_pressure
print(f"Calculated Differential Pressure: {head_pressure:.2f} bar")
`);
    } else if (presetType === 'malicious') {
      setCode(`import os
os.system('echo Attempting unauthorized host access')
`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content sandbox-modal">
        <div className="modal-header">
          <div className="modal-title-group">
            <Terminal size={20} color="#00f2fe" />
            <h2>Air-Gapped Sovereign Code Sandbox</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="sandbox-presets">
          <span>Presets:</span>
          <button onClick={() => loadPreset('vibration')}>Vibration FFT Math</button>
          <button onClick={() => loadPreset('pressure')}>Differential Pressure</button>
          <button onClick={() => loadPreset('malicious')} className="btn-preset-danger">Test Security Violation</button>
        </div>

        <div className="sandbox-editor-container">
          <textarea
            className="code-editor"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
          />
        </div>

        <div className="sandbox-actions">
          <button className="run-btn" onClick={handleRun} disabled={executing}>
            <Play size={14} />
            {executing ? 'Executing in Sandbox...' : 'Run Code in Sandbox'}
          </button>
        </div>

        {result && (
          <div className={`sandbox-result-box ${result.status.toLowerCase()}`}>
            <div className="result-header">
              <span className={`status-badge ${result.status}`}>{result.status}</span>
              <span className="time-badge">{result.execution_time_sec}s</span>
            </div>

            {result.violations && result.violations.length > 0 && (
              <div className="violations-block">
                <ShieldAlert size={16} color="#ef4444" />
                <div>
                  <strong>AST Security Violations Detected:</strong>
                  <ul>
                    {result.violations.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {result.stdout && (
              <div className="output-block">
                <label>Standard Output:</label>
                <pre>{result.stdout}</pre>
              </div>
            )}

            {result.stderr && (
              <div className="output-block stderr">
                <label>Standard Error / Output:</label>
                <pre>{result.stderr}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
