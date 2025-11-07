# Troubleshooting: Can't Get Past Sign-In Page

## Quick Debugging Steps

### Step 1: Check if Backend is Running

**Open a terminal and verify:**
```bash
# Check if Flask server is running
# You should see: "Running on http://127.0.0.1:5000"

# If not running, start it:
python app.py
```

**Common Issue:** Backend not running → Frontend can't authenticate

---

### Step 2: Check Browser Console

1. Open your browser (Chrome/Firefox/Edge)
2. Press **F12** to open Developer Tools
3. Click the **Console** tab
4. Try to sign up or log in
5. Look for error messages (red text)

**Common Errors:**
- `Failed to fetch` → Backend not running or CORS issue
- `401 Unauthorized` → Invalid credentials
- `Network Error` → Backend not accessible
- `CORS policy` → CORS configuration issue

---

### Step 3: Check Network Tab

1. In Developer Tools, click **Network** tab
2. Try to sign up or log in
3. Look for requests to `/api/auth/signup` or `/api/auth/login`
4. Click on the request to see:
   - **Status Code** (should be 200 or 201)
   - **Response** (check if it has `success: true`)

---

### Step 4: Verify API Endpoint

**Test if backend is accessible:**

Open browser and go to:
```
http://localhost:5000/api/health
```

**Expected Response:**
```json
{"success": true, "message": "API is healthy"}
```

**If this doesn't work:**
- Backend is not running
- Port 5000 is blocked
- Firewall is blocking the connection

---

## Common Issues & Solutions

### Issue 1: "Failed to fetch" Error

**Cause:** Backend server not running or not accessible

**Solution:**
1. Make sure Flask server is running:
   ```bash
   python app.py
   ```
2. Check terminal for errors
3. Verify server is on `http://localhost:5000`

---

### Issue 2: "CORS policy" Error

**Cause:** CORS not configured properly

**Solution:**
1. Make sure `flask-cors` is installed:
   ```bash
   pip install flask-cors
   ```
2. Check `app.py` has:
   ```python
   from flask_cors import CORS
   CORS(app)
   ```

---

### Issue 3: "Invalid credentials" on Signup

**Cause:** Username/email already exists or validation failed

**Solution:**
1. Try a different username/email
2. Make sure:
   - Username is at least 3 characters
   - Email is valid format
   - Password is at least 6 characters

---

### Issue 4: Form Submits but Nothing Happens

**Cause:** JavaScript error preventing form submission

**Solution:**
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check if `js/main.js` and `js/api.js` are loading
4. Verify all script tags in `index.html` are correct

---

### Issue 5: Database Errors

**Cause:** Database tables not created

**Solution:**
1. Make sure `intelliwheels.db` exists
2. If not, the database will be created automatically when you start Flask
3. Check `app.py` has `init_db()` called on startup

---

## Manual Testing

### Test Signup via Browser Console

Open browser console (F12) and run:

```javascript
// Test signup
fetch('http://localhost:5000/api/auth/signup', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'testuser',
        email: 'test@example.com',
        password: 'test123'
    })
})
.then(res => res.json())
.then(data => console.log('Signup Response:', data))
.catch(err => console.error('Error:', err));
```

**Expected Response:**
```json
{
    "success": true,
    "message": "Account created successfully",
    "token": "...",
    "user": {...}
}
```

### Test Login via Browser Console

```javascript
// Test login
fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'testuser',
        password: 'test123'
    })
})
.then(res => res.json())
.then(data => console.log('Login Response:', data))
.catch(err => console.error('Error:', err));
```

---

## Step-by-Step Debugging Checklist

- [ ] Backend server is running (`python app.py`)
- [ ] Backend is accessible (`http://localhost:5000/api/health`)
- [ ] Browser console shows no errors
- [ ] Network tab shows API requests
- [ ] API requests return 200/201 status
- [ ] Response contains `success: true`
- [ ] Error messages appear on page (if any)
- [ ] Database file exists (`intelliwheels.db`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)

---

## Still Not Working?

1. **Check Flask Terminal Output:**
   - Look for error messages when you try to sign up/login
   - Common errors: database locked, table doesn't exist, etc.

2. **Clear Browser Cache:**
   - Press Ctrl+Shift+Delete
   - Clear cache and cookies
   - Reload page

3. **Try Different Browser:**
   - Sometimes browser extensions interfere
   - Try incognito/private mode

4. **Check File Paths:**
   - Make sure `index.html` is opened from correct location
   - Scripts should load from `js/main.js`, `js/api.js`, etc.

5. **Verify API Base URL:**
   - Check `js/api.js` has correct `API_BASE_URL`
   - Should be: `http://localhost:5000/api`

---

## Quick Fix Script

If nothing works, try this:

```bash
# 1. Stop Flask server (Ctrl+C)

# 2. Delete database (will recreate)
rm intelliwheels.db  # Linux/Mac
del intelliwheels.db  # Windows

# 3. Restart Flask (will recreate database)
python app.py

# 4. Open index.html in browser
# 5. Try signing up with a new account
```

---

## Need More Help?

Share these details:
1. Browser console errors (F12 → Console)
2. Network tab request/response (F12 → Network)
3. Flask terminal output
4. What happens when you click Sign Up/Login (any error message?)

