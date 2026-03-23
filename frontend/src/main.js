import { getLatestSession, getSessionReport, getLiveFeed } from "./api.js"

const POLL_INTERVAL = 2000  // refresh every 2 seconds

let sessionId   = null
let chartPoints = []

// --- DOM ---
document.getElementById("app").innerHTML = `
  <div style="font-family:system-ui;max-width:900px;margin:0 auto;padding:24px">

    <h1 style="font-size:28px;font-weight:600;margin-bottom:4px">
      FocusLens AI
    </h1>
    <p id="session-label"
       style="color:#888;font-size:13px;margin-bottom:32px">
      Loading session...
    </p>

    <!-- score cards -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px">
      <div class="card">
        <div class="card-label">Focus score</div>
        <div class="card-value" id="focus-score">—</div>
      </div>
      <div class="card">
        <div class="card-label">Duration</div>
        <div class="card-value" id="duration">—</div>
      </div>
      <div class="card">
        <div class="card-label">Distractions</div>
        <div class="card-value" id="distractions">—</div>
      </div>
      <div class="card">
        <div class="card-label">Blink rate</div>
        <div class="card-value" id="blink-rate">—</div>
      </div>
    </div>

    <!-- live chart -->
    <div style="margin-bottom:32px">
      <h2 style="font-size:16px;font-weight:500;margin-bottom:12px">
        Live focus signal
      </h2>
      <canvas id="focus-chart" height="120"
        style="width:100%;border:1px solid #eee;border-radius:8px">
      </canvas>
    </div>

    <!-- gaze + rhythm -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      <div>
        <h2 style="font-size:16px;font-weight:500;margin-bottom:12px">
          Gaze distribution
        </h2>
        <div id="gaze-bars"></div>
      </div>
      <div>
        <h2 style="font-size:16px;font-weight:500;margin-bottom:12px">
          Rhythm
        </h2>
        <div id="rhythm-stats"></div>
      </div>
    </div>

  </div>
`

// --- styles ---
const style = document.createElement("style")
style.textContent = `
  body { margin:0; background:#fafafa; }
  .card {
    background:#fff;
    border:1px solid #eee;
    border-radius:10px;
    padding:16px;
  }
  .card-label { font-size:12px; color:#888; margin-bottom:6px; }
  .card-value  { font-size:28px; font-weight:600; color:#111; }
  .bar-row     { margin-bottom:8px; }
  .bar-label   { font-size:13px; color:#555; margin-bottom:3px; }
  .bar-track   {
    background:#f0f0f0; border-radius:4px; height:10px; overflow:hidden;
  }
  .bar-fill    { height:10px; border-radius:4px; background:#3b82f6; }
  .stat-row    {
    display:flex; justify-content:space-between;
    padding:10px 0; border-bottom:1px solid #f0f0f0;
    font-size:14px;
  }
  .stat-label { color:#555; }
  .stat-value { font-weight:500; color:#111; }
`
document.head.appendChild(style)

// --- canvas chart ---
const canvas = document.getElementById("focus-chart")
const ctx    = canvas.getContext("2d")

function drawChart(points) {
  const W = canvas.offsetWidth
  const H = canvas.offsetHeight
  canvas.width  = W
  canvas.height = H

  ctx.clearRect(0, 0, W, H)

  if (points.length < 2) return

  const step = W / (points.length - 1)

  // fill
  ctx.beginPath()
  ctx.moveTo(0, H)
  points.forEach((p, i) => {
    ctx.lineTo(i * step, H - (p * H * 0.8 + H * 0.1))
  })
  ctx.lineTo((points.length - 1) * step, H)
  ctx.closePath()
  ctx.fillStyle = "rgba(59,130,246,0.1)"
  ctx.fill()

  // line
  ctx.beginPath()
  points.forEach((p, i) => {
    const x = i * step
    const y = H - (p * H * 0.8 + H * 0.1)
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.strokeStyle = "#3b82f6"
  ctx.lineWidth   = 2
  ctx.stroke()
}

// --- gaze bars ---
function renderGaze(dist) {
  const zones = ["center","left","right","up","down"]
  document.getElementById("gaze-bars").innerHTML = zones.map(z => `
    <div class="bar-row">
      <div class="bar-label">${z} — ${dist[z].toFixed(1)}%</div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${dist[z]}%"></div>
      </div>
    </div>
  `).join("")
}

// --- rhythm stats ---
function renderRhythm(r) {
  const rows = [
    ["Avg focus duration",      `${r.avg_focus_duration_seconds}s`],
    ["Avg distraction duration", `${r.avg_distraction_duration_seconds}s`],
    ["Focus cycles",             r.focus_cycles],
    ["Longest focus",           `${r.longest_focus_seconds}s`],
  ]
  document.getElementById("rhythm-stats").innerHTML = rows.map(([l, v]) => `
    <div class="stat-row">
      <span class="stat-label">${l}</span>
      <span class="stat-value">${v}</span>
    </div>
  `).join("")
}

// --- update loop ---
async function update() {
  try {
    // get latest session if not set
    if (!sessionId) {
      const s  = await getLatestSession()
      sessionId = s.session_id
      document.getElementById("session-label").textContent =
        `Session: ${sessionId.slice(0, 8)}...`
    }

    // report
    const report = await getSessionReport(sessionId)
    document.getElementById("focus-score").textContent =
      report.focus_score.toFixed(1)
    document.getElementById("duration").textContent =
      `${report.duration_minutes.toFixed(1)} min`
    document.getElementById("distractions").textContent =
      report.distraction_count
    document.getElementById("blink-rate").textContent =
      `${report.blink_rate_per_minute}/min`

    renderGaze(report.gaze_distribution)
    renderRhythm(report.rhythm)

    // live feed for chart
    const feed = await getLiveFeed(sessionId)
    chartPoints = feed.frames.map(f => f.focused ? 1 : 0)
    drawChart(chartPoints)

  } catch(e) {
    console.error(e)
  }
}

// run immediately then every 2 seconds
update()
setInterval(update, POLL_INTERVAL)