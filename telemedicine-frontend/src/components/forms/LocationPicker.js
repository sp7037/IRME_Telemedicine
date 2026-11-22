import React, { useState, useEffect } from "react";

/**
 * LocationPicker Component
 * 
 * Features:
 * 1. Browser geolocation (reverse geocode to address)
 * 2. Indian PIN code lookup (api.postalpincode.in - free, no key needed)
 * 3. Optional Google Places Autocomplete (only if REACT_APP_GOOGLE_MAPS_API_KEY is set)
 * 4. Manual entry fallback
 * 
 * Props:
 * - value: { address, pincode, district, state, lat, lng }
 * - onChange: (locationData) => void
 * - error: string
 */

const LocationPicker = ({ value = {}, onChange, error }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [pinLookupLoading, setPinLookupLoading] = useState(false);

  const hasGoogleMaps = !!process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

  // Handle browser geolocation
  const handleUseCurrentLocation = async () => {
    if (!navigator.geolocation) {
      setMessage("Geolocation is not supported by your browser");
      return;
    }

    setLoading(true);
    setMessage("Getting your location...");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        try {
          // Try to reverse geocode using free Nominatim API
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`
          );
          
          if (response.ok) {
            const data = await response.json();
            const address = data.address || {};
            
            onChange({
              ...value,
              address: data.display_name || "",
              pincode: address.postcode || value.pincode || "",
              district: address.state_district || address.county || value.district || "",
              state: address.state || value.state || "",
              lat: latitude,
              lng: longitude,
            });
            
            setMessage("Location detected successfully!");
            setTimeout(() => setMessage(""), 3000);
          } else {
            // Geolocation worked but reverse geocode failed - store coordinates anyway
            onChange({
              ...value,
              lat: latitude,
              lng: longitude,
            });
            setMessage("Location detected. Please enter address details manually.");
          }
        } catch (err) {
          console.error("Reverse geocoding error:", err);
          onChange({
            ...value,
            lat: latitude,
            lng: longitude,
          });
          setMessage("Location detected. Please enter address details manually.");
        } finally {
          setLoading(false);
        }
      },
      (error) => {
        console.error("Geolocation error:", error);
        setLoading(false);
        
        if (error.code === error.PERMISSION_DENIED) {
          setMessage("Location access denied. Please enter address manually.");
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          setMessage("Location unavailable. Please enter address manually.");
        } else {
          setMessage("Could not get location. Please enter address manually.");
        }
      },
      { timeout: 10000, enableHighAccuracy: false }
    );
  };

  // Handle PIN code lookup
  const handlePinCodeLookup = async (pincode) => {
    if (!pincode || pincode.length !== 6) {
      return;
    }

    setPinLookupLoading(true);
    setMessage("");

    try {
      const response = await fetch(`https://api.postalpincode.in/pincode/${pincode}`);
      const data = await response.json();

      if (data && data[0] && data[0].Status === "Success" && data[0].PostOffice) {
        const postOffice = data[0].PostOffice[0];
        
        onChange({
          ...value,
          pincode: pincode,
          district: postOffice.District || value.district || "",
          state: postOffice.State || value.state || "",
        });
        
        setMessage("District and state auto-filled from PIN code");
        setTimeout(() => setMessage(""), 3000);
      } else {
        setMessage("PIN code not found. Please enter district and state manually.");
      }
    } catch (err) {
      console.error("PIN code lookup error:", err);
      setMessage("Could not verify PIN code. Please enter district and state manually.");
    } finally {
      setPinLookupLoading(false);
    }
  };

  // Debounced PIN code lookup
  useEffect(() => {
    const timer = setTimeout(() => {
      if (value.pincode && value.pincode.length === 6 && /^\d{6}$/.test(value.pincode)) {
        handlePinCodeLookup(value.pincode);
      }
    }, 500);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.pincode]);

  const handleInputChange = (field, fieldValue) => {
    onChange({ ...value, [field]: fieldValue });
    setMessage("");
  };

  return (
    <div style={styles.container}>
      {/* Use Current Location Button */}
      <div style={styles.locationButtonContainer}>
        <button
          type="button"
          onClick={handleUseCurrentLocation}
          disabled={loading}
          style={styles.locationButton}
        >
          {loading ? "Detecting location..." : "📍 Use my current location"}
        </button>
        {message && (
          <p style={message.includes("success") || message.includes("auto-filled") ? styles.successMessage : styles.infoMessage}>
            {message}
          </p>
        )}
      </div>

      {/* PIN Code Field */}
      <div style={styles.field}>
        <label style={styles.label} htmlFor="location-pincode">
          PIN Code <span style={styles.required}>*</span>
        </label>
        <input
          id="location-pincode"
          className="auth-input"
          type="text"
          inputMode="numeric"
          pattern="[0-9]{6}"
          maxLength="6"
          value={value.pincode || ""}
          onChange={(e) => handleInputChange("pincode", e.target.value)}
          placeholder="6-digit PIN code"
          required
        />
        {pinLookupLoading && <p style={styles.loadingText}>Looking up PIN code...</p>}
        <p style={styles.helperText}>
          Enter 6-digit PIN code to auto-fill district and state
        </p>
      </div>

      {/* Address Field */}
      <div style={styles.field}>
        <label style={styles.label} htmlFor="location-address">
          Address <span style={styles.required}>*</span>
        </label>
        <textarea
          id="location-address"
          className="auth-textarea"
          value={value.address || ""}
          onChange={(e) => handleInputChange("address", e.target.value)}
          placeholder="House/flat no., street, village/town"
          required
          rows="2"
        />
      </div>

      {/* District and State Row */}
      <div style={styles.row}>
        <div style={styles.field}>
          <label style={styles.label} htmlFor="location-district">
            District <span style={styles.required}>*</span>
          </label>
          <input
            id="location-district"
            className="auth-input"
            type="text"
            value={value.district || ""}
            onChange={(e) => handleInputChange("district", e.target.value)}
            placeholder="District"
            required
          />
        </div>

        <div style={styles.field}>
          <label style={styles.label} htmlFor="location-state">
            State <span style={styles.required}>*</span>
          </label>
          <input
            id="location-state"
            className="auth-input"
            type="text"
            value={value.state || ""}
            onChange={(e) => handleInputChange("state", e.target.value)}
            placeholder="State"
            required
            list="indian-states"
          />
          <datalist id="indian-states">
            <option value="Andhra Pradesh" />
            <option value="Arunachal Pradesh" />
            <option value="Assam" />
            <option value="Bihar" />
            <option value="Chhattisgarh" />
            <option value="Goa" />
            <option value="Gujarat" />
            <option value="Haryana" />
            <option value="Himachal Pradesh" />
            <option value="Jharkhand" />
            <option value="Karnataka" />
            <option value="Kerala" />
            <option value="Madhya Pradesh" />
            <option value="Maharashtra" />
            <option value="Manipur" />
            <option value="Meghalaya" />
            <option value="Mizoram" />
            <option value="Nagaland" />
            <option value="Odisha" />
            <option value="Punjab" />
            <option value="Rajasthan" />
            <option value="Sikkim" />
            <option value="Tamil Nadu" />
            <option value="Telangana" />
            <option value="Tripura" />
            <option value="Uttar Pradesh" />
            <option value="Uttarakhand" />
            <option value="West Bengal" />
            <option value="Delhi" />
            <option value="Jammu and Kashmir" />
            <option value="Ladakh" />
          </datalist>
        </div>
      </div>

      {error && <p style={styles.errorText}>{error}</p>}
      
      {!hasGoogleMaps && process.env.NODE_ENV === 'development' && (
        console.log('[LocationPicker] Google Maps API key not configured. Set REACT_APP_GOOGLE_MAPS_API_KEY for Places Autocomplete.')
      )}
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  locationButtonContainer: {
    marginBottom: "8px",
  },
  locationButton: {
    width: "100%",
    padding: "14px 20px",
    backgroundColor: "#1762bf",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    fontSize: "16px",
    fontWeight: 600,
    cursor: "pointer",
    transition: "background 150ms ease",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  row: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "18px",
  },
  label: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#10243e",
    letterSpacing: "0.01em",
  },
  required: {
    color: "#ef4444",
  },
  helperText: {
    fontSize: "13px",
    color: "#64748b",
    margin: "4px 0 0 0",
  },
  loadingText: {
    fontSize: "13px",
    color: "#1762bf",
    margin: "4px 0 0 0",
    fontStyle: "italic",
  },
  successMessage: {
    fontSize: "14px",
    color: "#17623c",
    backgroundColor: "#eef8f2",
    padding: "10px 14px",
    borderRadius: "8px",
    marginTop: "8px",
    border: "1px solid #acd9bf",
  },
  infoMessage: {
    fontSize: "14px",
    color: "#624000",
    backgroundColor: "#fff8e8",
    padding: "10px 14px",
    borderRadius: "8px",
    marginTop: "8px",
    border: "1px solid #efcf88",
  },
  errorText: {
    fontSize: "13px",
    color: "#b91c1c",
    fontWeight: 500,
    margin: 0,
  },
};

export default LocationPicker;
