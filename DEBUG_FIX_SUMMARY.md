# Debug & Fix Summary

## Root Causes Identified

### 1. **Double-Wrapped API Response** (Critical)
**File:** `static/js/app.js`  
**Problem:** The `api()` function was wrapping the backend response in another `{success, data}` layer:

```javascript
// BEFORE (broken)
return { success: true, data }; // data was already {success: true, data: [...]}
// Result: {success: true, data: {success: true, data: [...actual_projects...]}}

// AFTER (fixed)
return data; // Now returns {success: true, data: [...]} directly
```

**Impact:** Frontend received `{success: true, data: {success: true, data: [...]}}`, so `projects = result.data` became an **object** instead of an array, causing `projects.filter is not a function`.

### 2. **Insufficient Response Validation**
**File:** `static/js/projects.js`  
**Problem:** Frontend didn't validate that `projects` was actually an array before calling `.filter()`.

### 3. **Missing Debug Logging**
**Problem:** No visibility into what was being sent/received, making debugging difficult.

## Fixes Applied

### Backend (`app.py`)
1. ✅ Changed all API endpoints to return `{success: true, data: ...}` or `{success: false, error: ...}`
2. ✅ Added comprehensive try/catch with detailed error logging
3. ✅ Added global error handlers (404, 500, Exception)
4. ✅ Added debug logging for project creation: `[CREATE_PROJECT] ...`
5. ✅ Fault-tolerant project processing (bad projects are skipped, not crash)

### Frontend (`static/js/app.js`)
1. ✅ Fixed `api()` function to return raw backend response instead of double-wrapping
2. ✅ Added console logging for all API requests and responses
3. ✅ Better error messages in console

### Frontend (`static/js/projects.js`)
1. ✅ Added response normalization in `loadProjects()` - handles multiple response formats
2. ✅ Added defensive validation before calling `.filter()` on projects
3. ✅ Added array validation in `renderProjects()` with user-friendly error state
4. ✅ Added debug logging for create project payload and response
5. ✅ Better error handling with specific error messages
6. ✅ Skip null/undefined projects when filtering

## API Contract (Now Consistent)

### GET /api/projects
**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "name": "...",
      "dir": "...",
      "mode": "manual|auto",
      "status": "running|stopped|crashed|partial",
      "services_count": 1,
      "services": [...],
      ...
    }
  ]
}
```

### POST /api/projects
**Request:**
```json
{
  "name": "My Project",
  "dir": "C:/path/to/project",
  "mode": "manual",
  "services": [
    {
      "id": "default",
      "name": "Main",
      "cmd": "python run.py",
      "dir": "C:/path/to/project",
      "stop_cmd": ""
    }
  ]
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Project created successfully",
  "project": { ... }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Directory does not exist: C:/invalid/path"
}
```

## Response Normalization Logic

The frontend now handles multiple response formats gracefully:

```javascript
// Direct array
[...projects...]

// Standard format
{success: true, data: [...projects...]}

// Alternative format  
{success: true, projects: [...projects...]}

// Without success flag
{data: [...projects...]}

// Error format
{success: false, error: "..."}
```

## Debugging Output

### Backend Console
```
[CREATE_PROJECT] Creating project with data: {...}
[CREATE_PROJECT] Validation error: Directory does not exist: ...
[ERROR] get_projects: ...
```

### Browser Console
```
[API] GET /api/projects
[API] Response from /api/projects: {success: true, data: [...]}
[Projects] Raw API response: {success: true, data: [...]}
[Projects] Loaded 1 projects
[Projects] Sending create request with payload: {...}
[Projects] Create response: {success: true, project: {...}}
```

## Testing Checklist

After applying these fixes:

- [ ] Open browser console (F12)
- [ ] Refresh Projects page
- [ ] Check console shows: `[Projects] Loaded X projects`
- [ ] Projects should render correctly
- [ ] Click "Add Project" button
- [ ] Fill form with valid directory (must exist!)
- [ ] Check console shows payload being sent
- [ ] Submit form
- [ ] Check backend console shows validation (if any)
- [ ] Check frontend console shows response
- [ ] Project should appear in list
- [ ] All tabs (Projects, Dashboard, Settings) work

## Common 400 Errors

If POST /api/projects returns 400, check backend console for:

1. **"Missing required field: name"** → Enter a project name
2. **"Missing required field: dir"** → Enter a directory path
3. **"Missing required field: command"** → Service command is empty
4. **"Directory does not exist: ..."** → Path must be a real directory
5. **"Project with name '...' already exists"** → Use a unique name

## Data Safety

✅ Existing projects.json is preserved  
✅ Old format projects auto-convert to new format  
✅ One bad project won't crash the whole list  
✅ Validation errors show specific messages  
✅ Backend never returns HTML error pages to API calls
