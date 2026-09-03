package com.wiimote.andromote.ui.theme

import androidx.compose.ui.graphics.Color

// Website Backgrounds
val BgPrimary = Color(0xFF08080C)       // Deep Obsidian
val BgSecondary = Color(0xFF0E0E14)     // Midnight Dark
val BgSurface = Color(0xFF14141C)       // Card / Panel Surface
val BgElevated = Color(0xFF1A1A24)      // Elevated Components / Buttons

// Website Borders
val BorderSubtle = Color(0x14FFFFFF)    // rgba(255, 255, 255, 0.08)
val BorderMedium = Color(0x24FFFFFF)    // rgba(255, 255, 255, 0.14)
val BorderGlow = Color(0x665AE7FF)      // rgba(90, 231, 255, 0.40)

// Website Accents
val AccentCyan = Color(0xFF5AE7FF)      // Electric Cyan
val AccentDim = Color(0xFF3CC8E0)       // Cyan Dim
val AccentGreen = Color(0xFF4ADE80)     // Neon Success
val AccentRed = Color(0xFFFF6B6B)       // Coral Red (B button / Danger)
val AccentAmber = Color(0xFFFBBF24)     // Amber

// Website Typography
val TextPrimary = Color(0xFFF5F5F7)     // Primary Off-White
val TextSecondary = Color(0xFFA0A0AA)   // Secondary Silver-Gray
val TextTertiary = Color(0xFF60606A)    // Muted Dark Gray

// Controller Colors (Matching website phone mockup & cyber controller)
val WiimoteBody = Color(0xFF0E0E14)           // Midnight body
val WiimoteBorder = Color(0x28FFFFFF)         // Glass subtle border
val WiimoteDpad = Color(0xFF1B1B26)           // Dark graphite DPad
val WiimoteDpadPressed = Color(0xFF2E2E3E)    // Pressed DPad
val WiimoteButtonNormal = Color(0xFF1A1A24)   // Elevated button surface
val WiimoteButtonPressed = Color(0xFF2C2C3E)  // Pressed button
val WiimoteText = Color(0xFFF5F5F7)           // Crisp white label

// Backward-compatibility aliases
val DarkBackground = BgPrimary
val SurfaceDark = BgSurface
val PrimaryBlue = AccentCyan
