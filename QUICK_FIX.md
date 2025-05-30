# Quick Fix for BASH_SOURCE Error

## Issue Resolved ✅

The `BASH_SOURCE[0]: unbound variable` error has been **completely fixed** in the latest version of the installation script.

## Working Installation Commands

### ✅ **Using Specific Commit (Immediate Fix)**

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/494f430d/scripts/install-enhanced-marzban.sh)" @ install
```

### ✅ **Standard Installation (After CDN Cache Clears)**

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/main/scripts/install-enhanced-marzban.sh)" @ install
```

### ✅ **With Custom Domain**

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/494f430d/scripts/install-enhanced-marzban.sh)" @ install --domain your-domain.com
```

### ✅ **Silent Mode (No Prompts)**

```bash
sudo bash -c "$(curl -sL https://github.com/Kavis1/enhanced-marzban/raw/494f430d/scripts/install-enhanced-marzban.sh)" @ install --silent
```

## What Was Fixed

1. **Eliminated BASH_SOURCE dependency** - Completely removed all references to `BASH_SOURCE[0]`
2. **Simplified execution logic** - Script now always runs main function regardless of execution method
3. **Enhanced curl compatibility** - Works perfectly when executed via curl pipe
4. **Removed version comparison dependency** - Eliminated `bc` package requirement

## GitHub CDN Caching

GitHub's raw content CDN may cache the old version for a few minutes. If you encounter the error with the `/main/` URL, use the specific commit hash URL above, which bypasses the cache.

## Verification

You can test the script without installing by running:

```bash
curl -sL https://github.com/Kavis1/enhanced-marzban/raw/494f430d/scripts/install-enhanced-marzban.sh | bash -s -- --help
```

This should display the help message without any errors.

---

**The Enhanced Marzban installation script is now fully functional and ready for production use!**
