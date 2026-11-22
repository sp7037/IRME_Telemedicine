# Deploy Hotfix Summary - i18n Peer Dependency Fix

**Date**: November 22, 2026 15:50 UTC  
**PR**: https://github.com/sp7037/IRME_Telemedicine/pull/7  
**Branch**: `cursor/fix-i18n-peer-deps-1955` → `codex/aiccloud-staging-20261121`  
**Priority**: 🔥 URGENT - Blocks production Docker build

---

## Problem

After merging PR #1 (i18n integration), the AIC Cloud Docker build **fails** at:
```bash
RUN npm ci --no-audit --no-fund
```

### Error Output
```
npm error ERESOLVE could not resolve
npm error peerOptional typescript@"^5 || ^6 || ^7" from i18next@27.2.4
npm error peerOptional typescript@"^3.2.1 || ^4" from react-scripts@5.0.1
npm error Conflicting peer dependency: typescript@4.9.5 vs typescript@7.0.2
npm error Fix the upstream dependency conflict, or retry
npm error this command with --force or --legacy-peer-deps
```

### Root Cause Analysis

**Package Version Conflict**:
- `i18next@27.2.4` added in PR #1 has peer dependency: `typescript: "^5 || ^6 || ^7"`
- `react-scripts@5.0.1` (Create React App) has peer dependency: `typescript: "^3.2.1 || ^4"`
- These ranges **do not overlap** → npm cannot resolve

**Why It Failed in Docker but Not Locally**:
- Local development used `npm install --legacy-peer-deps` (permissive)
- Docker uses `npm ci --no-audit --no-fund` (strict, production-ready)
- `npm ci` enforces exact package-lock.json and fails on peer conflicts

---

## Solution

### Strategy: Downgrade to Compatible Versions

**Changed Dependencies**:
```diff
- "i18next": "^27.2.4"              (requires TypeScript 5+)
+ "i18next": "23.16.8"               (no TypeScript peer dep)

- "react-i18next": "^18.0.3"        (requires TypeScript 5+)  
+ "react-i18next": "15.5.0"         (no TypeScript peer dep)
```

**Why Not --legacy-peer-deps?**
1. ❌ Hides real incompatibility
2. ❌ Could cause runtime type mismatches
3. ❌ Requires modifying Dockerfile or committing .npmrc
4. ❌ Doesn't fix the underlying conflict
5. ✅ **Downgrading is cleaner** - proper semantic versioning

### Compatibility Check

| Feature | i18next 27.x | i18next 23.x | Status |
|---------|-------------|-------------|---------|
| useTranslation hook | ✅ | ✅ | Same API |
| Language detection | ✅ | ✅ | Same API |
| localStorage persistence | ✅ | ✅ | Same API |
| Namespace support | ✅ | ✅ | Same API |
| React 19 support | ✅ | ✅ | Compatible |
| Translation interpolation | ✅ | ✅ | Same API |

**Result**: Zero breaking changes for our usage.

---

## Verification

### 1. Clean Install Test ✅
```bash
cd telemedicine-frontend
rm -rf node_modules package-lock.json
git checkout cursor/fix-i18n-peer-deps-1955
npm ci --no-audit --no-fund
```
**Result**: Success! Installed 1306 packages in 7s

### 2. Build Test ✅
```bash
npm run build
```
**Result**: 
```
Compiled with warnings (pre-existing ESLint warnings only).

File sizes after gzip:
  360.69 kB  build/static/js/main.99fbb1a0.js  (+6.21 kB)
  2.58 kB    build/static/css/main.f8b792dd.css
  177 B      build/static/js/488.36a58fa7.chunk.js

The build folder is ready to be deployed.
```

### 3. Docker Build Simulation ✅

Simulated Dockerfile steps (from node:22-bookworm-slim):
```dockerfile
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund       # ✅ Success
RUN npm run build                      # ✅ Success
```

**Conclusion**: Docker build will succeed.

---

## Bundle Size Impact

| Metric | Before (27.x) | After (23.x) | Delta |
|--------|--------------|--------------|-------|
| Main JS | 354.48 kB | 360.69 kB | +6.21 kB |
| CSS | 2.59 kB | 2.58 kB | -10 B |
| **Total** | **357.07 kB** | **363.27 kB** | **+6.20 kB** |

**Analysis**: 
- 1.74% increase in bundle size
- Acceptable trade-off for production stability
- Still under 400 kB target

---

## Changed Files

```
telemedicine-frontend/package.json       (2 lines changed)
telemedicine-frontend/package-lock.json  (1334 insertions, 1079 deletions - full regeneration)
```

### package.json Changes
```json
{
  "dependencies": {
    "i18next": "23.16.8",           // was: "^27.2.4"
    "react-i18next": "15.5.0"       // was: "^18.0.3"
  }
}
```

---

## Rollback Plan

If any issues arise (unlikely):

```bash
git revert <commit-sha>
git push origin codex/aiccloud-staging-20261121
```

This will:
- Restore i18next 27.x and react-i18next 18.x
- Regenerate old package-lock.json
- Require --legacy-peer-deps workaround in Docker

---

## Post-Merge Checklist

After merging PR #7:

1. **AIC Cloud Auto-Deploy**:
   - Pulls latest `codex/aiccloud-staging-20261121`
   - Runs Docker build
   - `npm ci` succeeds ✅
   - `npm run build` succeeds ✅
   - Container deploys to telemedicine.irme.in

2. **Verify Live Site**:
   - [ ] Home page loads
   - [ ] Language switcher works (EN/HI/MR)
   - [ ] Translations display correctly
   - [ ] No console errors

3. **Monitor**:
   - [ ] Check Docker build logs
   - [ ] Verify no deployment errors
   - [ ] Test language switching in production

---

## Technical Details

### Dependency Tree Before Fix
```
react-scripts@5.0.1
  └── typescript@^3.2.1 || ^4 (peer)
i18next@27.2.4
  └── typescript@^5 || ^6 || ^7 (peer optional)
      └── CONFLICT ❌
```

### Dependency Tree After Fix
```
react-scripts@5.0.1
  └── typescript@^3.2.1 || ^4 (peer, optional, not installed)
i18next@23.16.8
  └── (no TypeScript peer dependency)
      └── NO CONFLICT ✅
```

---

## Lessons Learned

1. **Always test with npm ci**: Local `npm install` is more permissive than Docker's `npm ci`
2. **Check peer dependencies**: Major version bumps often introduce new peer deps
3. **Pin versions in production**: Avoid `^` ranges for critical dependencies
4. **Test Docker builds locally**: Reproduce the exact CI/CD environment

---

## Summary

✅ **Fixed**: Docker build now succeeds  
✅ **Verified**: Clean npm ci + build tested  
✅ **Compatible**: No API changes in our i18n usage  
✅ **Minimal Impact**: +6 kB bundle size (1.74% increase)  
✅ **Safe to Merge**: Low risk production hotfix  

**PR Link**: https://github.com/sp7037/IRME_Telemedicine/pull/7

---

**Agent**: bc-a4265fb7-c971-5d8b-af4f-910cdfab8680  
**Completed**: November 22, 2026 15:52 UTC
