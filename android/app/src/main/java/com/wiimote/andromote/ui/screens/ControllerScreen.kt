package com.wiimote.andromote.ui.screens

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.foundation.clickable
import androidx.compose.foundation.border
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.model.ConnectionState
import com.wiimote.andromote.ui.components.AirMousePad
import com.wiimote.andromote.ui.components.WiiRemotePad
import com.wiimote.andromote.ui.theme.*

enum class ControllerMode {
    WII_REMOTE,
    AIR_MOUSE
}

@Composable
fun ControllerScreen(
    connectionState: ConnectionState,
    isLandscape: Boolean = false,
    activeMode: ControllerMode = ControllerMode.WII_REMOTE,
    onModeChanged: (ControllerMode) -> Unit = {},
    isMotionActive: Boolean = true,
    isTouchpadFrozen: Boolean = false,
    onToggleMotion: () -> Unit = {},
    onToggleTouchpadFreeze: () -> Unit = {},
    onButtonEvent: (button: String, state: String) -> Unit,
    onTouchMove: (dx: Float, dy: Float) -> Unit = { _, _ -> },
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
                if (connectionState.isConnected && activeMode == ControllerMode.WII_REMOTE) {
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
                            text = if (isMotionActive) "Motion: ON" else "Motion: OFF",
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
                    Text("Recenter", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }

                IconButton(onClick = onNavigateToConnection) {
                    Icon(
                        imageVector = Icons.Default.Share,
                        contentDescription = "Wi-Fi Connection",
                        tint = AccentCyan
                    )
                }

                IconButton(onClick = onNavigateToCalibration) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "Settings",
                        tint = TextSecondary
                    )
                }
            }
        }

        // Controller Mode Switcher Bar (Wii Remote <-> Air Mouse)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 6.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(BgElevated)
                .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
                .padding(3.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            // Wii Remote Mode Tab
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (activeMode == ControllerMode.WII_REMOTE) AccentCyan else Color.Transparent)
                    .clickable { onModeChanged(ControllerMode.WII_REMOTE) }
                    .padding(vertical = 8.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Wii Remote",
                    color = if (activeMode == ControllerMode.WII_REMOTE) BgPrimary else TextSecondary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp
                )
            }

            // Air Mouse Mode Tab
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (activeMode == ControllerMode.AIR_MOUSE) AccentCyan else Color.Transparent)
                    .clickable { onModeChanged(ControllerMode.AIR_MOUSE) }
                    .padding(vertical = 8.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Air Mouse",
                    color = if (activeMode == ControllerMode.AIR_MOUSE) BgPrimary else TextSecondary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp
                )
            }
        }

        // Active Controller Interface Area
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentAlignment = Alignment.Center
        ) {
            when (activeMode) {
                ControllerMode.WII_REMOTE -> {
                    WiiRemotePad(
                        isLandscape = effectiveLandscape,
                        onButtonEvent = onButtonEvent
                    )
                }
                ControllerMode.AIR_MOUSE -> {
                    AirMousePad(
                        isMotionFrozen = isTouchpadFrozen,
                        onToggleFreeze = onToggleTouchpadFreeze,
                        onButtonEvent = onButtonEvent,
                        onRecenter = onRecenter,
                        onTouchMove = onTouchMove
                    )
                }
            }
        }
    }
}
