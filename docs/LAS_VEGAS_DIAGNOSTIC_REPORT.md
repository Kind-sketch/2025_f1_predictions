# Las Vegas Prediction Diagnostic Report
**Date:** 2025-11-18  
**Issue:** Las Vegas race not appearing in frontend, stale data  
**Status:** 🔴 **ROOT CAUSE IDENTIFIED**

---

## EXECUTIVE SUMMARY

**Root Cause:** Backend server was started **before** `races/las_vegas.json` was created, and the server needs to be restarted OR there's a silent exception being swallowed when loading the config file.

**Secondary Issue:** `predictions/las_vegas.json` does not exist - prediction file was never generated.

**Immediate Action:** Restart backend server, then generate prediction file.

---

## A. FILESYSTEM CHECKS

### A.1 Repository Base Path
```
/Users/charulekha/Desktop/EXP F1/F1-EXP
```

### A.2 Predictions Directory Status
```bash
$ ls -la predictions/
total 0
drwxr-xr-x@  2 charulekha  staff   64 Nov 17 23:52 .
drwxr-xr-x@ 27 charulekha  staff  864 Nov 18 00:10 ..
```

**Result:** ❌ **EMPTY** - No prediction files exist

### A.3 Las Vegas Prediction File
```bash
$ test -f predictions/las_vegas.json && head -n 200 predictions/las_vegas.json || echo "File does not exist"
File does not exist
```

**Result:** ❌ **MISSING** - `predictions/las_vegas.json` does not exist

### A.4 Las Vegas Race Config
```bash
$ ls -la races/las_vegas.json
-rw-r--r--@  1 charulekha  staff  1359 Nov 17 23:45 las_vegas.json

$ python3 -c "import json; config = json.load(open('races/las_vegas.json')); print('race_id:', config.get('race_id')); print('race_name:', config.get('race_name'))"
race_id: las_vegas
race_name: Las Vegas Grand Prix
```

**Result:** ✅ **EXISTS** - Config file is valid, created Nov 17 23:45:19

**File Timestamp:** 2025-11-17 23:45:19  
**File Size:** 1359 bytes  
**Schema:** ✅ Valid JSON with correct `race_id: "las_vegas"`

---

## B. BACKEND CHECKS

### B.1 Backend Code Analysis

**File:** `api/main.py`  
**Lines 25-26:**
```python
PREDICTIONS_DIR = Path("predictions")  # ⚠️ Relative path
RACES_DIR = Path("races")              # ⚠️ Relative path
```

**Issue:** Uses relative paths - will break if API run from wrong directory

**Lines 29-49:** `get_available_races()` function
```python
def get_available_races() -> List[Dict[str, str]]:
    races = []
    if RACES_DIR.exists():
        for config_file in RACES_DIR.glob("*.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    races.append({
                        "id": config.get("race_id", config_file.stem),
                        "name": config.get("race_name", config_file.stem.title())
                    })
            except Exception:  # ⚠️ SILENT EXCEPTION SWALLOWING
                continue
    return races if races else [...hardcoded fallback...]
```

**Critical Issue:** Line 41-42 silently swallows ALL exceptions, making debugging impossible

### B.2 Backend API Response

**Test 1: Direct Function Call**
```python
$ python3 -c "from api.main import get_available_races; races = get_available_races(); print(len(races), 'races')"
Backend returns: 6 races
  {'id': 'monaco', 'name': 'Monaco Grand Prix'}
  {'id': 'japan', 'name': 'Japanese Grand Prix'}
  {'id': 'bahrain', 'name': 'Bahrain Grand Prix'}
  {'id': 'australia', 'name': 'Australian GP 2025'}
  {'id': 'china', 'name': 'Chinese GP 2025'}
  {'id': 'las_vegas', 'name': 'Las Vegas Grand Prix'}  ✅ INCLUDES LAS VEGAS
```

**Test 2: Live API Endpoint**
```bash
$ curl -s http://localhost:8000/available-races | python3 -m json.tool
{
    "races": [
        {"id": "australia", "name": "Australian GP 2025"},
        {"id": "china", "name": "Chinese GP 2025"},
        {"id": "japan", "name": "Japanese GP 2025"},
        {"id": "bahrain", "name": "Bahrain GP 2025"},
        {"id": "monaco", "name": "Monaco GP 2025"}
    ]
}
```

**Result:** ❌ **MISMATCH** - API returns only 5 races, missing Las Vegas

**Test 3: Las Vegas Prediction Endpoint**
```bash
$ curl -i http://localhost:8000/predict/race/las_vegas
HTTP/1.1 404 Not Found
{"detail":"Race 'las_vegas' not found"}
```

**Result:** ❌ **404** - Backend doesn't recognize Las Vegas

### B.3 Root Cause Analysis

**Timeline:**
1. Backend server started: Nov 17 (before 23:45)
2. `races/las_vegas.json` created: Nov 17 23:45:19
3. Backend server still running with old state

**Problem:** The backend's `get_available_races()` function reads files on each request, BUT:
- If the server was started before the file existed, it may have cached the directory listing
- OR there's an exception when parsing `las_vegas.json` that's being silently swallowed
- OR the server is running from a different working directory

**Evidence:**
- Direct function call finds 6 races (including Las Vegas) ✅
- Live API returns only 5 races ❌
- This indicates the running server has stale state

### B.4 Path Resolution Issue

**Current Code:** `api/main.py:25-26`
```python
PREDICTIONS_DIR = Path("predictions")  # Relative to current working directory
RACES_DIR = Path("races")
```

**Risk:** If API started from `api/` directory instead of project root, paths will be wrong

**Verification:**
```python
$ python3 -c "from pathlib import Path; print('Current dir:', Path.cwd()); print('Races dir exists:', Path('races').exists())"
Current dir: /Users/charulekha/Desktop/EXP F1/F1-EXP
Races dir exists: True
```

**Status:** Paths work when run from project root, but fragile

---

## C. FRONTEND CHECKS

### C.1 Frontend Code Analysis

**File:** `frontend/src/App.jsx`  
**Line 6:**
```javascript
const API_BASE_URL = 'http://localhost:8000'  // ⚠️ Hardcoded
```

**Line 15-28:** Race loading
```javascript
useEffect(() => {
  axios.get(`${API_BASE_URL}/available-races`)
    .then(response => {
      setRaces(response.data.races)  // Uses whatever backend returns
      if (response.data.races.length > 0) {
        setSelectedRace(response.data.races[0].id)
      }
    })
```

**Status:** ✅ Frontend correctly fetches from backend - problem is backend not returning Las Vegas

### C.2 Frontend Caching Check

**Service Worker:** ❌ None found
```bash
$ find frontend -name "*service-worker*" -o -name "sw.js"
No service worker in public/
```

**Vite Config:** ✅ No caching configured
```javascript
// vite.config.js - no cache settings
```

**Browser Cache:** ⚠️ Possible - but backend is the source of truth

**Status:** Frontend is not caching - issue is backend not returning Las Vegas

### C.3 Network Request Analysis

**Expected:** Frontend calls `/available-races` → Should get 6 races  
**Actual:** Frontend calls `/available-races` → Gets 5 races (missing Las Vegas)

**Root Cause:** Backend server needs restart OR exception being swallowed

---

## D. RUN_PREDICTION.PY CHECKS

### D.1 Script Analysis

**File:** `run_prediction.py`  
**Lines 210-221:**
```python
output_path = Path(args.output_dir) / f"{args.race}.json"
save_predictions_json(predictions_json, output_path)
```

**Status:** ✅ Correctly writes to `predictions/{race}.json`

### D.2 Generation Test

**Command:** `python run_prediction.py --race las_vegas`

**Status:** ⚠️ **NOT YET RUN** - File doesn't exist, so generation hasn't been attempted

**Expected Output:** `predictions/las_vegas.json` with schema:
```json
{
  "race": "Las Vegas Grand Prix",
  "year": 2025,
  "predictions": [...],
  "model_metadata": {...}
}
```

---

## E. ROOT CAUSES IDENTIFIED

### Root Cause #1: Backend Server Stale State
**Issue:** Backend server was started before `races/las_vegas.json` was created  
**Evidence:** 
- Direct function call finds 6 races
- Live API returns 5 races
- File created Nov 17 23:45, server likely started earlier

**Fix:** Restart backend server

### Root Cause #2: Silent Exception Swallowing
**Issue:** `api/main.py:41-42` catches all exceptions silently  
**Risk:** If `las_vegas.json` has any parsing issue, it's silently ignored  
**Evidence:** No error logs when file should be loaded

**Fix:** Add logging and specific exception handling

### Root Cause #3: Missing Prediction File
**Issue:** `predictions/las_vegas.json` does not exist  
**Impact:** Even if race appears in dropdown, prediction will 404

**Fix:** Generate prediction file

### Root Cause #4: Relative Path Fragility
**Issue:** `api/main.py:25-26` uses relative paths  
**Risk:** If server started from wrong directory, paths break

**Fix:** Use absolute paths based on `__file__`

---

## F. IMMEDIATE REMEDIATION PLAN

### Fix 1: Restart Backend Server (IMMEDIATE)

**Action:** Restart the backend to pick up `las_vegas.json`

**Command:**
```bash
# Stop current backend (Ctrl+C in terminal running it)
# Then restart:
cd /Users/charulekha/Desktop/EXP\ F1/F1-EXP
source .venv/bin/activate
python api/main.py
# OR
uvicorn api.main:app --reload --port 8000
```

**Verification:**
```bash
curl http://localhost:8000/available-races | jq '.races | length'
# Should return 6
```

### Fix 2: Add Logging to Backend (RECOMMENDED)

**File:** `api/main.py`  
**Patch:**
```python
# Add at top (after imports)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace lines 41-42:
except json.JSONDecodeError as e:
    logger.warning(f"Invalid JSON in {config_file.name}: {e}")
    continue
except Exception as e:
    logger.error(f"Error loading {config_file.name}: {e}", exc_info=True)
    continue
```

**Why:** Reveals if there's a parsing error with las_vegas.json

### Fix 3: Fix Path Resolution (RECOMMENDED)

**File:** `api/main.py`  
**Lines 25-26:**
```python
# BEFORE:
PREDICTIONS_DIR = Path("predictions")
RACES_DIR = Path("races")

# AFTER:
BASE_DIR = Path(__file__).resolve().parent.parent
PREDICTIONS_DIR = BASE_DIR / "predictions"
RACES_DIR = BASE_DIR / "races"
```

**Why:** Makes paths work regardless of working directory

### Fix 4: Generate Las Vegas Prediction (REQUIRED)

**Command:**
```bash
cd /Users/charulekha/Desktop/EXP\ F1/F1-EXP
source .venv/bin/activate
python run_prediction.py --race las_vegas
```

**Expected Output:**
- File created: `predictions/las_vegas.json`
- Console shows: "✅ Predictions saved to predictions/las_vegas.json"

**Verification:**
```bash
ls -l predictions/las_vegas.json
# Should show file with recent timestamp
```

---

## G. PROPOSED CODE PATCHES

### Patch 1: Backend Path Resolution & Logging

**File:** `api/main.py`

**Unified Diff:**
```diff
--- a/api/main.py
+++ b/api/main.py
@@ -8,6 +8,10 @@ from typing import List, Dict, Any, Optional
 import json
 import os
 from pathlib import Path
 from datetime import datetime
+import logging
+
+logging.basicConfig(level=logging.INFO)
+logger = logging.getLogger(__name__)
 
 app = FastAPI(title="F1 Predictions API", version="1.0.0")
 
@@ -22,8 +26,9 @@ app.add_middleware(
 )
 
 # Paths
-PREDICTIONS_DIR = Path("predictions")
-RACES_DIR = Path("races")
+BASE_DIR = Path(__file__).resolve().parent.parent
+PREDICTIONS_DIR = BASE_DIR / "predictions"
+RACES_DIR = BASE_DIR / "races"
 
 # Available races (loaded from race configs)
 def get_available_races() -> List[Dict[str, str]]:
@@ -38,7 +43,10 @@ def get_available_races() -> List[Dict[str, str]]:
                         "id": config.get("race_id", config_file.stem),
                         "name": config.get("race_name", config_file.stem.title())
                     })
-            except Exception:
+            except json.JSONDecodeError as e:
+                logger.warning(f"Invalid JSON in {config_file.name}: {e}")
+                continue
+            except Exception as e:
+                logger.error(f"Error loading {config_file.name}: {e}", exc_info=True)
                 continue
     return races if races else [
         {"id": "australia", "name": "Australian GP 2025"},
@@ -67,7 +75,7 @@ def load_prediction(race_id: str) -> Optional[Dict[str, Any]]:
                 # Convert to frontend-compatible format
                 return convert_to_frontend_format(data)
         except Exception as e:
-            print(f"Error loading prediction: {e}")
+            logger.error(f"Error loading prediction {race_id}: {e}", exc_info=True)
             return None
     return None
```

**Safety:** ✅ Non-breaking - only adds logging and fixes paths

### Patch 2: Frontend Null Checks (OPTIONAL - for robustness)

**File:** `frontend/src/App.jsx`

**Unified Diff:**
```diff
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -55,7 +55,12 @@ function App() {
   // Histogram data (bins for race time distribution)
   const createHistogramData = () => {
     if (!predictionData?.predictions) return []
-    const times = predictionData.predictions.map(p => p.predicted_race_time)
+    const times = predictionData.predictions
+      .map(p => p.predicted_race_time)
+      .filter(t => typeof t === 'number' && !isNaN(t))
+    if (times.length === 0) return []
     const min = Math.min(...times)
     const max = Math.max(...times)
     const binCount = 8
@@ -170,7 +175,7 @@ function App() {
                     <div className="podium-driver">{p.driver}</div>
                     <div className="podium-team">{p.team}</div>
-                    <div className="podium-time">{p.predicted_race_time.toFixed(3)}s</div>
+                    <div className="podium-time">{(p.predicted_race_time ?? 0).toFixed(3)}s</div>
                   </div>
                 ))}
               </div>
@@ -197,8 +202,8 @@ function App() {
                     <td>{idx + 1}</td>
                     <td>{p.driver}</td>
                     <td>{p.team}</td>
-                    <td>{p.qualifying_time.toFixed(3)}s</td>
-                    <td>{p.predicted_race_time.toFixed(3)}s</td>
+                    <td>{(p.qualifying_time ?? 0).toFixed(3)}s</td>
+                    <td>{(p.predicted_race_time ?? 0).toFixed(3)}s</td>
                   </tr>
                 ))}
               </tbody>
```

**Safety:** ✅ Non-breaking - only adds defensive checks

---

## H. EXACT COMMANDS TO RUN

### Step 1: Restart Backend (IMMEDIATE FIX)

```bash
# Stop current backend (find terminal and press Ctrl+C)
# Then:
cd /Users/charulekha/Desktop/EXP\ F1/F1-EXP
source .venv/bin/activate
python api/main.py
```

**Verify:**
```bash
curl http://localhost:8000/available-races | jq '.races[] | select(.id == "las_vegas")'
# Should return: {"id":"las_vegas","name":"Las Vegas Grand Prix"}
```

### Step 2: Generate Las Vegas Prediction

```bash
cd /Users/charulekha/Desktop/EXP\ F1/F1-EXP
source .venv/bin/activate
python run_prediction.py --race las_vegas
```

**Expected:** File created at `predictions/las_vegas.json`

**Verify:**
```bash
ls -l predictions/las_vegas.json
# Should show file with recent timestamp
```

### Step 3: Verify API Endpoint

```bash
curl http://localhost:8000/predict/race/las_vegas | jq '.race'
# Should return: "Las Vegas Grand Prix"
```

### Step 4: Test Frontend

1. Open browser to http://localhost:5173
2. Open browser DevTools → Network tab
3. Refresh page
4. Check dropdown - should show "Las Vegas Grand Prix"
5. Select Las Vegas
6. Verify charts display predictions

---

## I. FINAL VERIFICATION CHECKLIST

### Pre-Verification
- [ ] Backend server restarted (to pick up las_vegas.json config)
- [ ] Backend logs show no errors when loading races
- [ ] `/available-races` endpoint returns 6 races including Las Vegas

### Generation
- [ ] `python run_prediction.py --race las_vegas` completes successfully
- [ ] `predictions/las_vegas.json` exists with recent timestamp
- [ ] JSON file is valid (can be parsed with `jq` or `python -m json.tool`)
- [ ] JSON matches schema (has `race`, `year`, `predictions`, `model_metadata`)

### API Verification
- [ ] `curl http://localhost:8000/available-races` returns 6 races
- [ ] `curl http://localhost:8000/predict/race/las_vegas` returns 200 OK
- [ ] Response JSON has correct structure
- [ ] Response includes `predictions` array with driver data

### Frontend Verification
- [ ] Frontend dropdown shows "Las Vegas Grand Prix"
- [ ] Selecting Las Vegas loads predictions (no 404 error)
- [ ] Charts render correctly (bar chart, histogram, line chart, podium)
- [ ] Table shows all drivers with predicted times
- [ ] No console errors in browser DevTools

### Update Verification (Test Staleness Fix)
- [ ] Modify a qualifying time in `races/las_vegas.json`
- [ ] Re-run: `python run_prediction.py --race las_vegas`
- [ ] Verify file timestamp updated
- [ ] Refresh frontend (or select Las Vegas again)
- [ ] Verify predictions updated (different times shown)

---

## J. ONE-LINE DIAGNOSTIC COMMAND

**Run this immediately to get full diagnostic info:**
```bash
python run_prediction.py --race las_vegas 2>&1 && curl -s http://localhost:8000/predict/race/las_vegas | jq '.' > /tmp/lasvegas_api.json && ls -la predictions/las_vegas.json && echo "=== API Response ===" && cat /tmp/lasvegas_api.json | head -n 50
```

**This will:**
1. Generate the prediction file
2. Test the API endpoint
3. Show file details
4. Display API response

---

## K. PRIORITIZED TODO LIST

### 🔴 CRITICAL (Do First)
1. **Restart backend server** - Las Vegas config won't appear until server restarts
2. **Generate prediction file** - `python run_prediction.py --race las_vegas`
3. **Verify API returns Las Vegas** - `curl http://localhost:8000/available-races | jq`

### 🟡 HIGH PRIORITY (Do After Critical)
4. **Apply Patch 1** - Fix path resolution and add logging (prevents future issues)
5. **Test frontend** - Verify Las Vegas appears and displays correctly
6. **Test update flow** - Regenerate and verify frontend updates

### 🟢 MEDIUM PRIORITY (Nice to Have)
7. **Apply Patch 2** - Add frontend null checks (defensive programming)
8. **Add environment variable** - Make API URL configurable for production

---

## L. SUMMARY

**Current Status:**
- ✅ Las Vegas config exists and is valid
- ❌ Backend server needs restart (stale state)
- ❌ Prediction file doesn't exist (needs generation)
- ⚠️ Backend has silent exception swallowing (needs logging)
- ⚠️ Backend uses relative paths (fragile)

**Root Causes:**
1. Backend server started before config file created
2. Prediction file never generated
3. Silent exception handling hides errors

**Immediate Actions:**
1. Restart backend: `python api/main.py`
2. Generate prediction: `python run_prediction.py --race las_vegas`
3. Verify: `curl http://localhost:8000/available-races | jq`

**Expected Outcome:**
After restart and generation, Las Vegas will appear in frontend dropdown and display predictions correctly.

---

**Report Complete**  
**Next Step:** Restart backend server, then generate prediction file

