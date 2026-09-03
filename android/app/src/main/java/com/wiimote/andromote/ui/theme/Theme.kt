package com.wiimote.andromote.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = AccentCyan,
    secondary = AccentDim,
    tertiary = AccentGreen,
    background = BgPrimary,
    surface = BgSurface,
    onPrimary = BgPrimary,
    onSecondary = BgPrimary,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    error = AccentRed,
    onError = BgPrimary
)

@Composable
fun AndromoteTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = Typography,
        content = content
    )
}
