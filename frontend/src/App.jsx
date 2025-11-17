import { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [races, setRaces] = useState([])
  const [selectedRace, setSelectedRace] = useState(null)
  const [predictionData, setPredictionData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Load available races
    axios.get(`${API_BASE_URL}/available-races`)
      .then(response => {
        setRaces(response.data.races)
        if (response.data.races.length > 0) {
          setSelectedRace(response.data.races[0].id)
        }
      })
      .catch(err => {
        console.error('Error loading races:', err)
        setError('Failed to load races. Make sure the backend API is running on port 8000.')
      })
  }, [])

  useEffect(() => {
    if (selectedRace) {
      setLoading(true)
      setError(null)
      axios.get(`${API_BASE_URL}/predict/race/${selectedRace}`)
        .then(response => {
          setPredictionData(response.data)
          setLoading(false)
        })
        .catch(err => {
          console.error('Error loading prediction:', err)
          setError('Failed to load prediction data.')
          setLoading(false)
        })
    }
  }, [selectedRace])

  // Prepare data for charts
  const chartData = predictionData?.predictions?.map(p => ({
    driver: p.driver,
    predictedTime: p.predicted_race_time,
    qualifyingTime: p.qualifying_time,
    team: p.team
  })) || []

  // Histogram data (bins for race time distribution)
  const createHistogramData = () => {
    if (!predictionData?.predictions) return []
    const times = predictionData.predictions.map(p => p.predicted_race_time)
    const min = Math.min(...times)
    const max = Math.max(...times)
    const binCount = 8
    const binSize = (max - min) / binCount
    
    const bins = Array(binCount).fill(0).map((_, i) => ({
      range: `${(min + i * binSize).toFixed(1)}-${(min + (i + 1) * binSize).toFixed(1)}s`,
      count: 0
    }))
    
    times.forEach(time => {
      const binIndex = Math.min(Math.floor((time - min) / binSize), binCount - 1)
      bins[binIndex].count++
    })
    
    return bins
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🏎️ F1 Race Predictions 2025</h1>
        <p>Machine Learning Model Predictions</p>
      </header>

      <div className="race-selector">
        <label htmlFor="race-select">Select Race: </label>
        <select 
          id="race-select"
          value={selectedRace || ''} 
          onChange={(e) => setSelectedRace(e.target.value)}
          disabled={loading}
        >
          {races.map(race => (
            <option key={race.id} value={race.id}>{race.name}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="loading">Loading predictions...</div>
      )}

      {predictionData && !loading && (
        <div className="predictions-container">
          <div className="race-info">
            <h2>{predictionData.race}</h2>
            <div className="model-info">
              <span>Model: {predictionData.model.type}</span>
              <span>MAE: {predictionData.model.mae}s</span>
            </div>
          </div>

          <div className="charts-grid">
            {/* Bar Chart - Predicted Race Times */}
            <div className="chart-card">
              <h3>Predicted Race Times</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="driver" />
                  <YAxis label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="predictedTime" fill="#8884d8" name="Predicted Race Time (s)" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Histogram - Time Distribution */}
            <div className="chart-card">
              <h3>Time Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={createHistogramData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" angle={-45} textAnchor="end" height={80} />
                  <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Line Chart - Qualifying vs Predicted */}
            <div className="chart-card">
              <h3>Qualifying vs Predicted Race Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="driver" />
                  <YAxis label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="qualifyingTime" stroke="#8884d8" name="Qualifying Time" />
                  <Line type="monotone" dataKey="predictedTime" stroke="#82ca9d" name="Predicted Race Time" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Podium Summary */}
            <div className="chart-card">
              <h3>🏁 Podium Predictions</h3>
              <div className="podium">
                {predictionData.predictions.slice(0, 3).map((p, idx) => (
                  <div key={p.driver} className={`podium-place place-${idx + 1}`}>
                    <div className="podium-position">{idx + 1}</div>
                    <div className="podium-driver">{p.driver}</div>
                    <div className="podium-team">{p.team}</div>
                    <div className="podium-time">{p.predicted_race_time.toFixed(3)}s</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Full Predictions Table */}
          <div className="predictions-table">
            <h3>Full Predictions</h3>
            <table>
              <thead>
                <tr>
                  <th>Position</th>
                  <th>Driver</th>
                  <th>Team</th>
                  <th>Qualifying Time</th>
                  <th>Predicted Race Time</th>
                </tr>
              </thead>
              <tbody>
                {predictionData.predictions.map((p, idx) => (
                  <tr key={p.driver}>
                    <td>{idx + 1}</td>
                    <td>{p.driver}</td>
                    <td>{p.team}</td>
                    <td>{p.qualifying_time.toFixed(3)}s</td>
                    <td>{p.predicted_race_time.toFixed(3)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Features Used */}
          <div className="features-info">
            <h3>Features Used</h3>
            <ul>
              {predictionData.features_used.map((feature, idx) => (
                <li key={idx}>{feature}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
