package com.wiimote.andromote.ui.screens

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.model.ConnectionState
import com.wiimote.andromote.ui.components.WiiRemotePad
import com.wiimote.andromote.ui.theme.*

@Composable
fun ControllerScreen(
    connectionState: ConnectionState,
    isLandscape: Boolean = false,
    isMotionActive: Boolean = true,
    onToggleMotion: () -> Unit = {},
    onButtonEvent: (button: String, state: String) -> Unit,
    onRecenter: () -> Unit,
    onNavigateToConnection: () -> Unit,
    onNavigateToCalibration: () -> Unit
) {
    val configuration = LocalConfiguration.current
    val effectiveLandscape = isLandscape || (configuration.orientation == Configuration.ORIENTATION_LANDSCAPE)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        // Top Connection Header Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(SurfaceDark)
                .padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Status and PC Name
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(if (connectionState.isConnected) AccentGreen else AccentRed)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Column {
                    Text(
                        text = if (connectionState.isConnected) connectionState.serverIp else "Disconnected",
                        color = TextPrimary,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        maxLines = 1
                    )
                    if (connectionState.isConnected) {
                        Text(
                            text = "${connectionState.latencyMs.toInt()} ms latency",
                            color = AccentCyan,
                            fontSize = 10.sp
                        )
                    }
                }
            }

            // Action Buttons: Motion Toggle, Recenter, Wi-Fi Setup, Calibration
            Row(
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (connectionState.isConnected) {
                    Button(
                        onClick = onToggleMotion,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isMotionActive) AccentCyan else BgElevated,
                            contentColor = if (isMotionActive) BgPrimary else TextSecondary
                        ),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = if (isMotionActive) "🖱️ Motion: ON" else "⏸️ Motion: OFF",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Button(
                    onClick = onRecenter,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentGreen,
                        contentColor = BgPrimary
                    ),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text("🎯 Recenter", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }

                IconButton(onClick = onNavigateToConnection) {
                    Text("📶", fontSize = 18.sp)
                }

                IconButton(onClick = onNavigateToCalibration) {
                    Text("⚙️", fontSize = 18.sp)
                }
            }
        }

        // Wii Remote Controller Area
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentAlignment = Alignment.Center
        ) {
            WiiRemotePad(
                isLandscape = effectiveLandscape,
                onButtonEvent = onButtonEvent
            )
        }
    }
}
