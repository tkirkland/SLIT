# SLIT Testing Guide

## 🧪 Testing the Configuration System

### Quick Test (Non-Interactive)
The installer now defaults to **dry-run mode** and automatically uses test configuration:

```bash
python installer.py
```

This will:
- ✅ Use `test_install.conf` automatically if present
- ✅ Run in dry-run mode (no actual changes)
- ✅ Complete all 5 installation phases
- ✅ Show detailed progress output

### Interactive Configuration Test
To test the interactive configuration prompts:

```bash
python run_interactive_test.py
```

This will:
- 🔧 Walk through all configuration prompts
- 📝 Show auto-detected defaults
- 💾 Save configuration to a temporary file
- 📄 Display the generated configuration

### Hardware Detection Tests
To test drive enumeration and Windows detection:

```bash
python test_hardware.py
```

This validates:
- 🔍 Drive enumeration (both mock and real hardware)
- 🪟 Windows detection with confidence levels
- ⚠️ Safety filtering (removes Windows/removable drives)
- 📊 Comprehensive hardware analysis

### Interactive Drive Selection Test
To test the interactive drive selection interface:

```bash
python test_interactive_drives.py
```

This demonstrates:
- 🔍 Real-time drive detection
- 🪟 Windows installation warnings
- ✅ Safety indicators for each drive
- 🛡️ Confirmation prompts for dangerous operations

### User Account Prompt Flow Test
To test the specific user account prompt order:

```bash
python test_user_prompts.py
```

This tests the correct prompt sequence:
1. 👤 **User full name** (GECOS field, defaults to "KDE User")
2. 🔤 **Username** (Linux username validation)
3. 🔐 **Passwordless sudo** (y/n confirmation)
4. 🏠 **Hostname** (system hostname)

### Configuration System Tests
To test all configuration functionality:

```bash
python test_config.py
```

This validates:
- ✅ Auto-detection (locale, timezone, network interface)
- ✅ Configuration validation
- ✅ File save/load operations
- ✅ Data integrity verification
- ✅ Corruption detection

## 📁 Test Files

- **`test_install.conf`** - Pre-configured test settings for quick testing
- **`test_user_prompts.py`** - Test user account prompt flow (fullname → username → sudo → hostname)
- **`test_hardware.py`** - Test hardware detection and drive enumeration  
- **`test_interactive_drives.py`** - Test interactive drive selection with Windows detection
- **`run_interactive_test.py`** - Interactive configuration testing
- **`test_config.py`** - Comprehensive system testing

## 🎯 Test Scenarios

### 1. Default Test Run
```bash
python installer.py
```
**Expected Result:** 
- Loads test_install.conf
- Runs all 5 phases in dry-run mode
- Shows "DRY-RUN COMPLETED" message

### 2. Interactive Configuration
```bash
# Move test config temporarily
mv test_install.conf test_install.conf.bak
python installer.py
# Then restore: mv test_install.conf.bak test_install.conf
```
**Expected Result:**
- Prompts for all configuration settings
- Shows auto-detected defaults
- Validates input in real-time

### 3. Configuration Validation
Edit `test_install.conf` and add invalid values to test validation:
```json
{
  "target_drive": "invalid-drive",
  "username": "123invalid",
  "hostname": ""
}
```
**Expected Result:**
- Validation errors displayed
- Specific error messages for each field

### 4. Corrupted Configuration
```bash
echo "{ invalid json" > test_install.conf
python installer.py
```
**Expected Result:**
- Corruption detected
- Prompt to delete corrupted file (in interactive mode)

## 🔧 Development Testing

### Enable Real Installation Mode
To test actual installation (use with caution):

1. Edit `installer.py` line 744:
```python
dry_run = False  # Change from True to False
```

2. Ensure proper permissions:
```bash
sudo python installer.py
```

**⚠️ WARNING:** This will make actual system changes!

### Debug Logging
Enable detailed logging:

```bash
export DEBUG=1
python installer.py
```

View logs:
```bash
tail -f logs/slit-install-*.log
```

## ✅ Test Checklist

- [ ] Default dry-run test completes successfully
- [ ] Interactive configuration accepts valid inputs
- [ ] Configuration validation catches errors
- [ ] File save/load operations work correctly
- [ ] Auto-detection finds system settings
- [ ] Corruption detection works properly
- [ ] All 5 installation phases execute
- [ ] Logging captures all operations

## 📊 Expected Output

### Successful Test Run
```
🧪 TESTING MODE: Dry-run enabled by default
============================================================
📁 Found test_install.conf - using test configuration

--- Phase 1 of 5 ---
[DRY-RUN] Starting SystemPreparation
[... all phases complete ...]

============================================================
DRY-RUN COMPLETED - No changes were made
============================================================

Installer scaffold test completed successfully!
```

### Test Configuration Values
The included `test_install.conf` uses:
- **Target Drive:** `/dev/nvme0n1`
- **User Full Name:** `Test User`
- **Username:** `testuser`
- **Passwordless Sudo:** `true`
- **Hostname:** `slit-test`
- **Network:** DHCP
- **Locale:** `en_US.UTF-8`
- **Timezone:** `America/New_York`

These values are safe for testing and validation.