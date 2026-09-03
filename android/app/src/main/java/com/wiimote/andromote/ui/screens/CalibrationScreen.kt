package com.wiimote.andromote.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.model.MotionTelemetry
import com.wiimote.andromote.ui.theme.*

@Composable
fun CalibrationScreen(
    telemetry: MotionTelemetry,
    onRecenter: () -> Unit
) {
    var sensitivity by remember { mutableFloatStateOf(18f) }
    var smoothing by remember { mutableFloatStateOf(0.30f) }
    var deadzone by remember { mutableFloatStateOf(0.04f) }
    var invertX by remember { mutableStateOf(false) }
    var invertY by remember { mutableStateOf(false) }
    var showDiagnostics by remember { mutableStateOf(true) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Motion Tuning & Calibration",
            color = TextPrimary,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 14.dp)
        )

        // Recenter Neutral Orientation Button
        Button(
            onClick = onRecenter,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = AccentGreen,
                contentColor = BgPrimary
            ),
            shape = RoundedCornerShape(10.dp)
        ) {
            Text("🎯 Recenter Neutral Orientation", fontSize = 16.sp, fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Sliders Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                // Sensitivity
                Text(text = "Sensitivity: ${sensitivity.toInt()}x", color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Slider(
                    value = sensitivity,
                    onValueChange = { sensitivity = it },
                    valueRange = 5f..50f,
                    colors = SliderDefaults.colors(
                        thumbColor = AccentCyan,
                        activeTrackColor = AccentCyan,
                        inactiveTrackColor = BgElevated
                    )
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Smoothing
                Text(text = "Smoothing: ${(smoothing * 100).toInt()}%", color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Slider(
                    value = smoothing,
                    onValueChange = { smoothing = it },
                    valueRange = 0f..0.8f,
                    colors = SliderDefaults.colors(
                        thumbColor = AccentCyan,
                        activeTrackColor = AccentCyan,
                        inactiveTrackColor = BgElevated
                    )
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Deadzone
                Text(text = "Deadzone: ${String.format("%.2f", deadzone)}", color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Slider(
                    value = deadzone,
                    onValueChange = { deadzone = it },
                    valueRange = 0f..0.15f,
                    colors = SliderDefaults.colors(
                        thumbColor = AccentCyan,
                        activeTrackColor = AccentCyan,
                        inactiveTrackColor = BgElevated
                    )
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Invert Toggles
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Invert X Axis", color = TextPrimary)
                    Switch(
                        checked = invertX,
                        onCheckedChange = { invertX = it },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = BgPrimary,
                            checkedTrackColor = AccentCyan,
                            uncheckedThumbColor = TextTertiary,
                            uncheckedTrackColor = BgElevated
                        )
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Invert Y Axis", color = TextPrimary)
                    Switch(
                        checked = invertY,
                        onCheckedChange = { invertY = it },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = BgPrimary,
                            checkedTrackColor = AccentCyan,
                            uncheckedThumbColor = TextTertiary,
                            uncheckedTrackColor = BgElevated
                        )
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Diagnostic HUD Section
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Live Sensor Diagnostics", color = AccentCyan, fontWeight = FontWeight.Bold, fontSize = 15.sp)
            TextButton(onClick = { showDiagnostics = !showDiagnostics }) {
                Text(if (showDiagnostics) "Hide" else "Show")
            }
        }

        if (showDiagnostics) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text("Orientation (Euler)", color = TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    Text("Yaw: ${String.format("%.1f", telemetry.yawDeg)}°  |  Pitch: ${String.format("%.1f", telemetry.pitchDeg)}°  |  Roll: ${String.format("%.1f", telemetry.rollDeg)}°", color = TextPrimary)

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Gyroscope (rad/s)", color = TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    Text("X: ${String.format("%.2f", telemetry.gyroX)}  |  Y: ${String.format("%.2f", telemetry.gyroY)}  |  Z: ${String.format("%.2f", telemetry.gyroZ)}", color = TextPrimary)

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Accelerometer (m/s²)", color = TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    Text("X: ${String.format("%.2f", telemetry.accelX)}  |  Y: ${String.format("%.2f", telemetry.accelY)}  |  Z: ${String.format("%.2f", telemetry.accelZ)}", color = TextPrimary)

                    Spacer(modifier = Modifier.height(10.dp))

                    Text("Sensor Frame Count: ${telemetry.packetCount}", color = TextSecondary, fontSize = 12.sp)
                }
            }
        }
    }
}
